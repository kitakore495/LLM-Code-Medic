import ast
import json
import os
import re
import shutil
from dotenv import load_dotenv
from typing import Dict, List, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from src.agent.prompts import DIAGNOSE_SYSTEM_PROMPT, REPAIR_SYSTEM_PROMPT
from src.agent.state import AgentState
from src.llm.llm_invoker import LLMInvoker
from src.llm.provider_router import ProviderRouter
from src.quality.patch_quality_gate import PatchQualityGate
from src.quality.policy_gate import run_policy_gate
from src.quality.repairability_gate import (
    RepairabilityGate,
    prompt_user_authorization,
)
from src.quality.semantic_patch_gate import SemanticPatchGate
from src.tools.executor import CodeExecutor
from src.tools.ast_resolver import (
    expand_target_files
)
from src.tools.scanner import scan_in_memory

# 初始化环境变量
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
ENV_PATH = os.path.join(ROOT_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH, override=True)


def parse_patch_response(raw_text: str):
    repo_updates = {}
    pattern = re.compile(
        r"<<<FILE_PATH:\s*(.*?)>>>(.*?)<<<FILE_END>>>", re.DOTALL
    )
    matches = pattern.findall(raw_text)
    print(f"""
📝 已解析补丁块数量: {len(matches)}""")

    for relative_path, code in matches:
        relative_path = relative_path.strip().replace("\\", "/")
        relative_path = re.sub(r"^(tests/[^/]+/|v\d+/)", "", relative_path)
        repo_updates[relative_path] = code.strip()
        print(f"""    -> 已更新: {relative_path} ({len(code)} bytes)""")

    return repo_updates

def build_ast_context(state):

    import json

    export_table = state.get(
        "export_table",
        {}
    )

    call_graph = state.get(
        "call_graph",
        {}
    )

    import_graph = state.get(
        "import_graph",
        {}
    )

    return f"""
========================
【EXPORT TABLE】
========================
{json.dumps(
    export_table,
    indent=2,
    ensure_ascii=False
)}

========================
【CALL GRAPH】
========================
{json.dumps(
    call_graph,
    indent=2,
    ensure_ascii=False
)}

========================
【IMPORT GRAPH】
========================
{json.dumps(
    import_graph,
    indent=2,
    ensure_ascii=False
)}
"""
def build_symbol_index(state):

    export_table = state.get(
        "export_table",
        {}
    )

    index = {}

    for (
        file_path,
        info
    ) in export_table.items():

        for symbol in info.get(
            "exports",
            []
        ):

            index[
                symbol
            ] = file_path

    return index

def resolve_symbol(
    state,
    symbol_name
):

    symbol_index = (
        build_symbol_index(
            state
        )
    )

    if symbol_name in symbol_index:

        return symbol_index[
            symbol_name
        ]

    symbol_lower = (
        symbol_name.lower()
    )

    for (
        symbol,
        file_path
    ) in symbol_index.items():

        if (
            symbol.lower()
            == symbol_lower
        ):

            return file_path

    for (
        symbol,
        file_path
    ) in symbol_index.items():

        if (
            symbol_lower
            in symbol.lower()
        ):

            return file_path

    return None

def create_diagnose_llm():
    return (
        ProviderRouter.get_diagnose_provider(),
        ProviderRouter.get_diagnose_model(),
    )


def create_repair_llm():
    return (
        ProviderRouter.get_repair_provider(),
        ProviderRouter.get_repair_model(),
    )


def build_gate_constraints(
    semantic_reason: str, sandbox_stderr: str, repair_attempts: int
) -> str:
    rules = []
    if not semantic_reason and not sandbox_stderr:
        return "N/A"

    reason_lower = (semantic_reason or "").lower()
    stderr_lower = (sandbox_stderr or "").lower()

    if "magic number" in reason_lower or "rule-1" in reason_lower:
        rules += [
            "- FORBIDDEN: do NOT replace runtime inputs with arbitrary constants",
            "- FORBIDDEN: do NOT add fallback return values on invalid-input paths",
            "- REQUIRED: thresholds must be named constants derivable from repo semantics",
        ]
    if "shim" in reason_lower or "rule-3" in reason_lower:
        rules += [
            "- FORBIDDEN: do NOT introduce compatibility wrappers with default arguments",
            "- FORBIDDEN: do NOT add delegation-only helper functions",
        ]
    if "签名" in semantic_reason or "rule-5" in reason_lower:
        rules += [
            "⚠️ RULE-5 VIOLATION DETECTED:",
            "- FORBIDDEN: do NOT modify existing public function signatures.",
            "- ACTION REQUIRED: You MUST revert the function signature to its original state.",
            "- SOLUTION: Find another way to pass data, such as importing constants from config.py directly.",
        ]
    if "公式常量" in semantic_reason or "rule-4" in reason_lower:
        rules.append(
            "- FORBIDDEN: preserve all arithmetic constants in existing functions; extraction to named constant is allowed but original value must remain in expression"
        )
    if "rule-2" in reason_lower or "异常吞噬" in semantic_reason:
        rules += [
            "- FORBIDDEN: except blocks must re-raise or escalate; never swallow",
            "- FORBIDDEN: do NOT use bare except or except Exception without re-raise",
        ]
    if "rule-6" in reason_lower or "caller 盲区" in semantic_reason:
        rules += [
            "⚠️  CALLER_BLINDSPOT DETECTED — MANDATORY CONSTRAINT:",
            "- The callee already has a raise guard. It is CORRECT. Do NOT modify it.",
            "- ROOT_CAUSE_CLASS MUST be treated as [CALLER_VIOLATED] for this repair.",
            "- You MUST include the caller file in your repair.",
            "- Identify the caller's invalid argument value and correct it.",
            "- The corrected value MUST be derivable from repository context.",
            "- If no valid value can be derived: output ESCALATE_REQUIRED.",
        ]
    if repair_attempts >= 2 and (
        "valueerror" in stderr_lower or "error" in stderr_lower
    ):
        rules += [
            "⚠️  SANDBOX_LOOP DETECTED — MANDATORY CONSTRAINT:",
            f"""  repair_attempts={repair_attempts}, sandbox still failing with exception.""",
            "- If callee already has `raise` after previous repairs: DO NOT touch callee guard.",
            "- Perform LOOP_CHECK: does the caller pass a value that violates callee contract?",
            "- If YES: fix the caller. The callee is already correct.",
            "- If the caller's value cannot be corrected without inventing a business value:",
            """  output ESCALATE_REQUIRED and stop.""",
        ]

    return "\n".join(rules) if rules else "N/A"


import json
import re
from langchain_core.messages import SystemMessage, HumanMessage

def diagnose_node(state: AgentState):
    print(f"\n🚀 [Diagnose] 第 {state.get('repair_attempts', 0) + 1} 轮诊断...")
    provider, model_name = create_diagnose_llm()
    print(f"🧠 Diagnose Provider: {provider} | Model: {model_name}")

    repo_snapshot_text = "\n".join(
        [
            f"""
===== FILE: {path} =====
{code}"""
            for path, code in state["repo_files"].items()
        ]
    )
# ----------------------------------------------------------------------
    # 【核心拦截器】：若不是首轮，强制基于大模型修改后的 state["repo_files"] 重新编译 AST
    # ----------------------------------------------------------------------
    if state.get("repair_attempts", 0) > 0:
        print("🔄 [AST] 检测到上一轮修复已变更源码，正在纯内存动态重新扫描依赖拓扑...")
        
        # 消费内存中的最新代码快照，计算新图谱
        new_export, new_call, new_import = scan_in_memory(state["repo_files"])
        
        # 覆盖写回当前图状态机，彻底清除认知盲区
        state["export_table"] = new_export
        state["call_graph"] = new_call
        state["import_graph"] = new_import
        print("✅ [AST] 依赖图谱与导出表内存对齐完毕。")

    # ======================================================================
    # 随后的索引提取函数将完美继承第二轮/最新轮次的最新数据！
    # ======================================================================
    _current_export_table = state.get("export_table", {})
    _current_call_graph = state.get("call_graph", {})
    _current_import_graph = state.get("import_graph", {})
    
    _current_symbol_index = build_symbol_index(state)
    ast_context = build_ast_context(state)

    # --------------------------------------------------------
    # 2. 规范化调试打印输出
    # --------------------------------------------------------
    print("\n📊 ExportTable:")
    print(len(_current_export_table))

    print("📊 SymbolIndex:")
    print(len(_current_symbol_index))

    print("📊 CallGraph:")
    print(len(_current_call_graph))

    print("📊 ImportGraph:")
    print(len(_current_import_graph))

    repair_history_text = "\n\n".join(state.get("repair_history", []))
    repair_attempts = state.get("repair_attempts", 0)
    sandbox_stderr = state.get("sandbox_stderr", "")
    
    loop_hint = ""
    if repair_attempts >= 1 and sandbox_stderr:
        loop_hint = f"""========================
【⚠️ VERIFY-LOOP SIGNAL】
repair_attempts = {repair_attempts}
sandbox 仍然失败，stderr 如下：
{sandbox_stderr}
执行 PHASE 2 VERIFY-LOOP DETECTION：
LOOP_CHECK_1: stderr 与上一轮是否为同类异常？
LOOP_CHECK_2: 上一轮是否只修改了 callee 文件？
LOOP_CHECK_3: callee 是否已包含 raise？
如果三项均为 YES：ROOT_CAUSE_CLASS 必须重新判定为 [CALLER_VIOLATED]，且 TARGET_FILES 必须包含 caller 文件。禁止继续只修改 callee。"""

    # --------------------------------------------------------
    # 3. 干净装配的组装 Prompt（移除了冗余的旧 Dump）
    # --------------------------------------------------------
    user_prompt = f"""请诊断当前项目故障。
禁止修复。禁止输出代码。
你的职责仅为：
1. 根因定位
2. ROOT_CAUSE_CLASS 判定
3. REPAIR_SCOPE 推断
4. TARGET_FILES 推断
5. BUG_INVENTORY 全量扫描（见下方约束）

========================
【历史根因分析】
========================
{state.get('analysis', '首次诊断')}

========================
【AST Symbol Index】
========================
{json.dumps(_current_symbol_index, indent=2, ensure_ascii=False)}

========================
【AST工程索引】
========================
{ast_context}

========================
【项目源码】
========================
{repo_snapshot_text}

========================
【Patch Gate Failure】
========================
{state.get('patch_quality_reason', '')}

========================
【Semantic Gate Failure】
========================
{state.get('semantic_gate_reason', '')}

========================
【历史失败修复】
========================
{repair_history_text}

========================
【最近一次 stderr】
========================
{sandbox_stderr}
{loop_hint}

========================
【沙箱执行约定 — Import 路径规则】
========================
所有源码文件在沙箱执行时写入同一执行目录（扁平布局）。
import 只能使用模块名本身（= 文件名去掉 .py），不允许含目录层级。
正确：from validator import validate_dataset
错误：from some.nested.path.validator import validate_dataset

========================
【BUG_INVENTORY 强制扫描约束】
========================
在输出 TARGET_FILES 之前，必须对所有涉及文件执行完整扫描：
CHECK-1: 被 import 的模块名是否存在于 repo_files？
CHECK-2: 被 import 的 symbol 是否在该模块中实际定义？（必须读源码确认）
CHECK-3: 调用的函数名是否与 callee 定义完全匹配？
CHECK-4: 传入的参数名称和数量是否与函数签名完全匹配？（必须读 callee 源码）
CHECK-5: 字符串/路径字面量参数是否可被 repo_files 中的具名常量替代？
将所有不合法条目列入 BUG_INVENTORY。repair 必须一次性修复全部条目。

========================
【诊断约束】
========================
程序运行成功 ≠ 修复成功。
Caller correction 只有在 ROOT_CAUSE_CLASS == [CALLER_VIOLATED] 且修正值可从项目常量、配置、命名语义、文档契约中推导时允许。
如果无法推导：输出 ESCALATE_REQUIRED。
严格按照 DIAGNOSE_SYSTEM_PROMPT 格式输出，必须包含 LOOP_CHECK 和 BUG_INVENTORY 段落。"""

    response = LLMInvoker.invoke(
        provider=provider,
        model_name=model_name,
        messages=[
            SystemMessage(content=DIAGNOSE_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ],
        temperature=0.1,
    )
    analysis = response.content

    target_files = []
    files_match = re.search(
        r"TARGET_FILES:\s*(\[.*?\])", analysis, re.DOTALL | re.IGNORECASE
    )
    if files_match:
        try:
            parsed = json.loads(files_match.group(1).replace("'", '"'))
            if isinstance(parsed, list):
                target_files = [
                    p.strip() for p in parsed if isinstance(p, str)
                ]
        except:
            pass

    cleaned = []
    for p in target_files:
        p = p.replace("\\", "/").strip()
        p = re.sub(r"^(tests/[^/]+/|v\d+/)", "", p)
        if p.endswith(".py") and ".." not in p:
            cleaned.append(p)

    # 1. 先去重并获取初步列表
    target_files = list(dict.fromkeys(cleaned))

    # --------------------------------------------------------
    # 4. 安全调用全依赖感知的扩展函数（完美对齐 5 参数签名）
    # --------------------------------------------------------
    target_files = expand_target_files(
        target_files,
        _current_export_table,
        _current_call_graph,
        _current_import_graph,
        _current_symbol_index
    )

    # 5. 最终赋值兜底
    target_files = (
        target_files 
        or list(state["repo_files"].keys())
    )
    print(f"🎯 目标文件: {target_files}")
    
    return {
        **state,
        "analysis": analysis,
        "target_files": target_files
    }

def repair_node(state: AgentState):
    print("🛠️ [Repair] 正在生成多文件补丁...")
    provider, model_name = create_repair_llm()
    print(f"🧠 Repair Provider: {provider} | Model: {model_name}")

    full_repo_snapshot = "\n".join(
        [
            f"""
===== FILE: {path} =====
{code}"""
            for path, code in state["repo_files"].items()
        ]
    )
    editable_targets = state.get("target_files", [])
    repair_history_text = "\n\n".join(state.get("repair_history", []))
    gate_constraints = build_gate_constraints(
        state.get("semantic_gate_reason", ""),
        state.get("sandbox_stderr", ""),
        state.get("repair_attempts", 0),
    )

    from src.quality.repairability_gate import build_authorization_context

    authorization_context = build_authorization_context(state)

    user_prompt = f"""请修复当前项目。

========================
【根因分析（含 BUG_INVENTORY）】
========================
{state.get('analysis', '未提供根因分析')}

========================
【完整项目源码（只读参考）】
========================
{full_repo_snapshot}

========================
【允许修改文件】
========================
{editable_targets}
规则：可读取整个 repo，只允许输出 target_files 中的文件，其他文件仅作为 dependency / contract 参考。

========================
【Semantic Gate Failure】
========================
{state.get('semantic_gate_reason', '')}

========================
【Policy Gate Failure】
========================
{state.get('policy_gate_reason', '')}

========================
【历史失败修复】
========================
{repair_history_text}

========================
【最近一次 stderr】
========================
{state.get('sandbox_stderr', '')}

========================
【修复要求】
========================
1. 严格遵循 ROOT_CAUSE_CLASS
2. 修复 BUG_INVENTORY 中全部条目（禁止 waterfall repair）
3. 禁止发明 business 值
4. 无合法方案时：ESCALATE_REQUIRED: reason

========================
【🛡️ 动态门禁强制约束】
========================
{gate_constraints}

{authorization_context}"""

    response = LLMInvoker.invoke(
        provider=provider,
        model_name=model_name,
        messages=[
            SystemMessage(content=REPAIR_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ],
        temperature=0.1,
    )
    raw_patch = response.content
    print(f"""
================ LLM PATCH RAW ================
{raw_patch}
=========================================""")

    history = list(state.get("repair_history", []))
    history.append(
        f"""[LLM PATCH]
attempt={state.get('repair_attempts', 0)}
{raw_patch}"""
    )

    updates = parse_patch_response(raw_patch)
    merged_repo_files = dict(state["repo_files"])
    merged_repo_files.update(updates)

    return {
        **state,
        "repo_files": merged_repo_files,
        "repaired_repo_files": merged_repo_files,
        "repair_history": history,
        "repair_attempts": state.get("repair_attempts", 0) + 1,
    }


def repairability_gate_node(state: AgentState):
    print("""
🔍 [Repairability Gate] 检查当前问题是否可自动修复...""")
    gate = RepairabilityGate()
    repairable, reason, options, needs_decision = gate.check(state)
 
    print(f"[DEBUG] repair_attempts = {state.get('repair_attempts', 0)}")
    print(f"[DEBUG] sandbox_stderr exists = {bool(state.get('sandbox_stderr'))}")
    print(f"[DEBUG] semantic_gate_reason = {state.get('semantic_gate_reason') or 'OK'}")
    print(f"[DEBUG] policy_gate_reason = {state.get('policy_gate_reason') or ''}")
 
    if repairable:
        print("✅ [RepairabilityGate] 当前仍可继续修复")
        return {
            **state,
            "repairable": True,
            "repair_status": "REPAIRABLE",
            "repairability_reason": reason,
            "repair_options": options,
            "needs_user_decision": needs_decision,
        }
 
    # 不可修复 → 在节点里做用户交互，把授权写入 state
    print(f"""❌ [RepairabilityGate] 当前约束下无法自动修复
原因: {reason}""")
    history = list(state.get("repair_history", []))
    history.append(f"""[RepairabilityGate]
UNREPAIRABLE_UNDER_CONSTRAINTS
reason={reason}""")
 
    should_continue_flag, mode, auth_context = prompt_user_authorization(
        unrepairable_reason=reason,
        analysis=state.get("analysis", ""),
    )
 
    if not should_continue_flag:
        return {
            **state,
            "repairable": False,
            "repair_status": "TERMINATED_BY_USER",
            "repairability_reason": reason,
            "repair_options": options,
            "needs_user_decision": needs_decision,
            "is_fixed": False,
            "repair_history": history,
            # 明确清空授权，防止残留
            "repair_mode": "STRICT",
            "_pending_repair_mode": "",
            "_pending_authorization": "",
        }
 
    # 用户授权继续 → 直接写入 repair_mode，不走 _pending 中转
    print(f"🔁 [RepairabilityGate] 用户授权 {mode} 模式，继续修复")
    return {
        **state,
        "repairable": True,
        "repair_status": "AUTHORIZED",
        "repairability_reason": reason,
        "repair_options": options,
        "needs_user_decision": needs_decision,
        "repair_history": history,
        "repair_mode": mode,              # ← 直接写入，不用 _pending 中转
        "user_authorization": auth_context,
        "is_unrepairable": False,
        "_pending_repair_mode": "",
        "_pending_authorization": "",
    }
 

def semantic_patch_gate_node(state: AgentState):
    print("""
🧠 [Semantic Patch Gate] 正在检查语义补丁质量...""")
    gate = SemanticPatchGate()
    passed, reason = gate.check(
        repo_files=state.get("repo_files", {}),
        original_repo_files=state.get("original_repo_files", {}),
        analysis=state.get("analysis", ""),
        target_files=state.get("target_files", []),
        sandbox_stderr=state.get("sandbox_stderr", ""),
    )

    history = list(state.get("repair_history", []))
    if passed:
        print("✅ [Semantic Patch Gate] 检查通过")
    else:
        print(f"""❌ [Semantic Patch Gate] 检查失败
原因: {reason}""")
        history.append(
            f"""[Semantic Patch Failure]
reason={reason}
repair_attempts={state.get('repair_attempts', 0)}"""
        )

    return {
        **state,
        "semantic_gate_passed": passed,
        "semantic_gate_reason": reason,
        "repair_history": history,
    }


def verify_node(state: AgentState):
    print("""
🧪 [Verify] 正在进行沙箱验证...""")
    current_repo_files = state.get("repo_files", {})
    executor = CodeExecutor(repo_root=state["repo_root"])
    success, error_log = False, ""

    try:
        res = executor.run_v3_validation(current_repo_files)
        if isinstance(res, tuple):
            success = res[0]
            if len(res) > 1:
                error_log = res[1]
        elif hasattr(res, "returncode"):
            success = res.returncode == 0
            error_log = (
                f"""STDOUT: {getattr(res,'stdout','')}
STDERR: {getattr(res,'stderr','')}"""
                if not success
                else ""
            )
        else:
            success = bool(res)
    except Exception as e:
        import traceback

        success = False
        error_log = f"""Critical sandbox wrapper crash: {str(e)}
{traceback.format_exc()}"""

    if success:
        print("""
🎉 [Graph] 沙箱验证完全通过！""")
    else:
        print("""
❌ [Graph] 沙箱验证遭遇失败！""")

    return {
        **state,
        "is_fixed": success,
        "verify_passed": success,
        "sandbox_stderr": (
            "" if success else (error_log or "Unknown sandbox error")
        ),
        "semantic_gate_reason": (
            "ok" if success else state.get("semantic_gate_reason", "")
        ),
        "policy_gate_reason": (
            "" if success else state.get("policy_gate_reason", "")
        ),
    }


def patch_quality_gate_node(state: AgentState):
    print("""
🧪 [Patch Quality Gate] 正在检查补丁质量...""")
    gate = PatchQualityGate()
    passed, reason = gate.check(
        analysis=state.get("analysis", ""),
        original_files=state.get("original_repo_files", {}),
        repaired_files=state.get("repo_files", {}),
        target_files=state.get("target_files", []),
    )

    history = list(state.get("repair_history", []))
    if not passed:
        print(f"❌ [Patch Quality Gate] 检查失败: {reason}")
        history.append(
            f"""[Patch Gate Failure]
reason={reason}
repair_attempts={state.get('repair_attempts', 0)}"""
        )
    else:
        print("✅ [Patch Quality Gate] 检查通过")

    return {
        **state,
        "patch_quality_passed": passed,
        "patch_quality_reason": reason,
        "repair_history": history,
    }


def policy_gate_node(state: AgentState):
    print("""
🧠 [Policy Gate] 正在检查修复策略违规...""")
    repair_mode = state.get("repair_mode", "STRICT")
    print(f"[DEBUG] policy_gate: repair_mode={repair_mode}")

    ok, reason = run_policy_gate(
        state["original_repo_files"],
        state["repo_files"],
        allow_caller_mutation=(repair_mode in ("GUIDED", "OVERRIDE")),
    )

    if not ok:
        print(f"❌ [PolicyGate] 检查失败: {reason}")
        return {**state, "policy_gate_passed": False, "policy_gate_reason": reason}

    print("✅ [PolicyGate] 检查通过")
    return {**state, "policy_gate_passed": True, "policy_gate_reason": ""}


def inject_authorization_node(state: AgentState):
    mode = state.get("_pending_repair_mode", "STRICT")
    auth = state.get("_pending_authorization", "")
    print(f"[DEBUG] inject_authorization: mode={mode}")
    return {
        **state,
        "repair_mode": mode,
        "user_authorization": auth,
        "_pending_repair_mode": "",
        "_pending_authorization": "",
        "repairable": True,
        "is_unrepairable": False,
    }


def should_continue_after_patch_gate(state: AgentState):
    if state.get("patch_quality_passed", False):
        print("✅ [Gate] Patch Quality 通过")
        return "semantic_patch_gate"
    if state.get("repair_attempts", 0) >= 5:
        print("💀 Patch Gate 超过最大修复次数")
        return END
    return "repair"


def should_continue_after_semantic_gate(state: AgentState):
    if state.get("semantic_gate_passed", False):
        print("✅ [Gate] Semantic Patch 通过")
        return "policy_gate"
    if state.get("repair_attempts", 0) >= 5:
        print("💀 Semantic Gate 超过最大修复次数")
        return END
    return "repair"


def should_continue_after_policy_gate(state: AgentState):
    """policy_gate 失败有两种情况：

    - STRICT 模式下 caller mutation → 走 repairability_gate 让用户决策
    - GUIDED/OVERRIDE 模式下其他违规 → 直接回 repair 重试
    """
    if state.get("policy_gate_passed", False):
        print("✅ [Gate] Policy Gate 通过")
        return "verify"

    repair_mode = state.get("repair_mode", "STRICT")
    if repair_mode in ("GUIDED", "OVERRIDE"):
        print(f"⚠️ [PolicyGate] {repair_mode} 模式下违规，回 repair 重试")
        return "repair"

    print("⚠️ [PolicyGate] STRICT 模式下检测到违规，送入 RepairabilityGate")
    return "repairability_gate"


def should_continue_after_repairability(state: AgentState):
    if state.get("repair_attempts", 0) >= 5:
        print("""
💀 [Routing] 达到最大修复轮次 (5次)，强制终止""")
        return "stop"
 
    repair_status = state.get("repair_status", "REPAIRABLE")
    print(f"""
[DEBUG] repair_status = {repair_status}""")
    print(f"[DEBUG] repair_mode = {state.get('repair_mode', 'STRICT')}")
 
    if repair_status == "TERMINATED_BY_USER":
        print("🛑 自动修复终止（用户决策）")
        return "stop"
 
    if repair_status in ("REPAIRABLE", "AUTHORIZED"):
        print("🔁 [RepairabilityGate] 继续修复")
        return "diagnose"
 
    # repairable=False 且没有授权 → stop
    if not state.get("repairable", True):
        print("🛑 自动修复终止")
        return "stop"
 
    return "diagnose"
 

def should_continue_after_verify(state: AgentState) -> str:
    if state.get("verify_passed", False) or state.get("is_fixed", False):
        print("""
🏁 [Graph-Routing] 沙箱测试完全通过！正在退出状态机并完成修复。...""")
        return "end"

    print("""
🔁 [Graph-Routing] 沙箱仍存在报错，正在送入 RepairabilityGate 分析...""")
    return "repairability_gate"


def create_v4_medic_graph():
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("diagnose", diagnose_node)
    workflow.add_node("repair", repair_node)
    workflow.add_node("patch_quality_gate", patch_quality_gate_node)
    workflow.add_node("semantic_patch_gate", semantic_patch_gate_node)
    workflow.add_node("policy_gate", policy_gate_node)
    workflow.add_node("repairability_gate", repairability_gate_node)
    workflow.add_node("verify", verify_node)
    workflow.add_node("inject_authorization", inject_authorization_node)

    # 添加固定边
    workflow.add_edge(START, "diagnose")
    workflow.add_edge("diagnose", "repair")
    workflow.add_edge("repair", "patch_quality_gate")
    workflow.add_edge("inject_authorization", "diagnose")

    # 添加条件边
    workflow.add_conditional_edges(
        "patch_quality_gate",
        should_continue_after_patch_gate,
        {"repair": "repair", "semantic_patch_gate": "semantic_patch_gate", END: END},
    )
    workflow.add_conditional_edges(
        "semantic_patch_gate",
        should_continue_after_semantic_gate,
        {"repair": "repair", "policy_gate": "policy_gate", END: END},
    )
    workflow.add_conditional_edges(
        "policy_gate",
        should_continue_after_policy_gate,
        {
            "verify": "verify",
            "repair": "repair",
            "repairability_gate": "repairability_gate",
        },
    )
    workflow.add_conditional_edges(
        "verify",
        should_continue_after_verify,
        {"end": END, "repairability_gate": "repairability_gate"},
    )
    workflow.add_conditional_edges(
        "repairability_gate",
        should_continue_after_repairability,
        {
            "diagnose": "diagnose",
            "inject_authorization": "inject_authorization",
            "stop": END,
        },
    )

    return workflow.compile()