import os
import re

from dotenv import load_dotenv

# =========================================================
# 强制加载 .env
# =========================================================
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

ENV_PATH = os.path.join(ROOT_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH, override=True)

from typing import TypedDict
from typing import List
from typing import Dict

from src.agent.state import AgentState
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage

from src.agent.prompts import DIAGNOSE_SYSTEM_PROMPT, REPAIR_SYSTEM_PROMPT
from src.tools.executor import CodeExecutor
from src.llm.provider_router import ProviderRouter
from src.llm.llm_invoker import LLMInvoker
from src.quality.patch_quality_gate import PatchQualityGate
from src.quality.semantic_patch_gate import SemanticPatchGate
from src.quality.policy_gate import run_policy_gate
from langgraph.graph import (
    StateGraph,
    START,
    END
)

# =========================================================
# PATCH PARSER
# =========================================================
def parse_patch_response(raw_text: str):
    repo_updates = {}
    pattern = re.compile(
        r"<<<FILE_PATH:\s*(.*?)>>>"
        r"(.*?)"
        r"<<<FILE_END>>>",
        re.DOTALL
    )

    matches = pattern.findall(raw_text)
    print(f"\n📝 已解析补丁块数量: {len(matches)}")

    for relative_path, code in matches:
        relative_path = relative_path.strip().replace("\\", "/")
        relative_path = re.sub(r"^(tests/[^/]+/)", "", relative_path)
        relative_path = re.sub(r"^(v\d+/)", "", relative_path)

        repo_updates[relative_path] = code.strip()
        print(f"   -> 已更新: {relative_path} ({len(code)} bytes)")

    return repo_updates

# =========================================================
# LLM 配置
# =========================================================
def create_diagnose_llm():
    provider = ProviderRouter.get_diagnose_provider()
    model_name = ProviderRouter.get_diagnose_model()
    print(f"🧠 Diagnose Provider: {provider} | Model: {model_name}")
    return provider, model_name

def create_repair_llm():
    provider = ProviderRouter.get_repair_provider()
    model_name = ProviderRouter.get_repair_model()
    print(f"🧠 Repair Provider: {provider} | Model: {model_name}")
    return provider, model_name

# =========================================================
# Diagnose Node
# =========================================================
def build_gate_constraints(
    semantic_reason: str,
    sandbox_stderr: str,
    repair_attempts: int,
) -> str:
    rules = []
 
    if not semantic_reason and not sandbox_stderr:
        return "N/A"
 
    reason_lower = (semantic_reason or "").lower()
    stderr_lower = (sandbox_stderr or "").lower()
 
    # ── 来自 SemanticGate 的约束 ──────────────────────────────
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
        rules.append("- FORBIDDEN: do NOT modify existing public function signatures")
 
    if "公式常量" in semantic_reason or "rule-4" in reason_lower:
        rules.append(
            "- FORBIDDEN: preserve all arithmetic constants in existing functions; "
            "extraction to named constant is allowed but original value must remain in expression"
        )
 
    if "rule-2" in reason_lower or "异常吞噬" in semantic_reason:
        rules += [
            "- FORBIDDEN: except blocks must re-raise or escalate; never swallow",
            "- FORBIDDEN: do NOT use bare except or except Exception without re-raise",
        ]
 
    # ── RULE-6 Caller 盲区（最高优先级约束）────────────────────
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
 
    # ── Sandbox 循环检测（verify 反复失败，callee 已有 raise）───
    # 当 repair_attempts >= 2 且 stderr 里反复出现同类异常时触发
    if (
        repair_attempts >= 2
        and ("valueerror" in stderr_lower or "error" in stderr_lower)
    ):
        rules += [
            "⚠️  SANDBOX_LOOP DETECTED — MANDATORY CONSTRAINT:",
            f"  repair_attempts={repair_attempts}, sandbox still failing with exception.",
            "- If callee already has `raise` after previous repairs: DO NOT touch callee guard.",
            "- Perform LOOP_CHECK: does the caller pass a value that violates callee contract?",
            "- If YES: fix the caller. The callee is already correct.",
            "- If the caller's value cannot be corrected without inventing a business value:",
            "  output ESCALATE_REQUIRED and stop.",
        ]
 
    return "\n".join(rules) if rules else "N/A"
 
 
# =========================================================
# diagnose_node
# =========================================================
def diagnose_node(state: AgentState):
    print(f"\n🚀 [Diagnose] 第 {state.get('repair_attempts', 0) + 1} 轮诊断...")
    provider, model_name = create_diagnose_llm()
 
    repo_snapshot_text = "\n".join([
        f"\n===== FILE: {path} =====\n{code}"
        for path, code in state["repo_files"].items()
    ])
    repair_history_text = "\n\n".join(state.get("repair_history", []))
    repair_attempts = state.get("repair_attempts", 0)
    sandbox_stderr = state.get("sandbox_stderr", "")
 
    # 循环检测提示：当 repair_attempts >= 1 且有 stderr 时注入
    loop_hint = ""
    if repair_attempts >= 1 and sandbox_stderr:
        loop_hint = f"""
========================
【⚠️ VERIFY-LOOP SIGNAL】
========================
repair_attempts = {repair_attempts}
sandbox 仍然失败，stderr 如下：
{sandbox_stderr}
 
执行 PHASE 2 VERIFY-LOOP DETECTION：
- LOOP_CHECK_1: stderr 与上一轮是否为同类异常？
- LOOP_CHECK_2: 上一轮是否只修改了 callee 文件？
- LOOP_CHECK_3: callee 是否已包含 raise？
如果三项均为 YES → ROOT_CAUSE_CLASS 必须重新判定为 [CALLER_VIOLATED]，
且 TARGET_FILES 必须包含 caller 文件。
禁止继续只修改 callee。
""".strip()
 
    user_prompt = f"""
请诊断当前项目故障。
禁止修复。禁止输出代码。
你的职责仅为：
  1. 根因定位
  2. ROOT_CAUSE_CLASS 判定
  3. REPAIR_SCOPE 推断
  4. TARGET_FILES 推断
 
========================
【历史根因分析】
========================
{state.get('analysis', '首次诊断')}
 
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
【诊断约束】
========================
程序运行成功 ≠ 修复成功。
 
FORBIDDEN:
1. 修改调用参数仅为了让程序运行成功
2. 用任意常量替换运行时输入
3. 发明仓库中不存在的业务阈值
4. 为绕过异常而改变参数
5. 根据单个测试表现猜测业务规则
 
Caller correction 只有在以下条件满足时允许：
  1. ROOT_CAUSE_CLASS == [CALLER_VIOLATED]
  AND
  2. 修正值可从项目常量、配置、命名语义、文档契约、已有不变量中推导
如果无法推导：输出 ESCALATE_REQUIRED，不要臆造业务值。
 
严格按照 DIAGNOSE_SYSTEM_PROMPT 格式输出，包含 LOOP_CHECK 段落。
""".strip()
 
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
 
    # 解析 TARGET_FILES
    target_files = []
    files_match = re.search(
        r"TARGET_FILES:\s*(\[.*?\])", analysis, re.DOTALL | re.IGNORECASE
    )
    if files_match:
        try:
            import json
            parsed = json.loads(files_match.group(1).replace("'", '"'))
            if isinstance(parsed, list):
                target_files = [p.strip() for p in parsed if isinstance(p, str)]
        except Exception:
            pass
 
    cleaned = []
    for p in target_files:
        p = p.replace("\\", "/").strip()
        p = re.sub(r"^(tests/[^/]+/|v\d+/)", "", p)
        if p.endswith(".py") and ".." not in p:
            cleaned.append(p)
    target_files = list(dict.fromkeys(cleaned)) or list(state["repo_files"].keys())
 
    print(f"🎯 目标文件: {target_files}")
    return {
        **state,
        "analysis": analysis,
        "target_files": target_files,
    }
 
 
# =========================================================
# repair_node
# =========================================================
def repair_node(state: AgentState):
    print("🛠️ [Repair] 正在生成多文件补丁...")

    provider, model_name = create_repair_llm()

    repo_snapshot_text = "\n".join([
        f"\n===== FILE: {path} =====\n{code}"
        for path, code in state["repo_files"].items()
        if (
            not state.get("target_files")
            or path in state.get("target_files", [])
        )
    ])

    repair_history_text = "\n\n".join(
        state.get("repair_history", [])
    )

    user_prompt = f"""
请修复当前项目。

【根因分析】
{state.get("analysis", "未提供根因分析")}

【需要修复的源码】
{repo_snapshot_text}

【Semantic Gate Failure】
{state.get("semantic_gate_reason", "")}

【Policy Gate Failure】
{state.get("policy_gate_reason", "")}

【历史失败修复】
{repair_history_text}

【修复要求】
1. 严格遵循 ROOT_CAUSE_CLASS。
2. 若 Diagnose 出现 ESCALATE_REQUIRED：
   立即停止修复，不允许乱猜业务值。
3. 禁止硬编码业务输入值。
4. 禁止修改公式和阈值。
5. 无合法方案时必须输出：
ESCALATE_REQUIRED: reason
""".strip()

    response = LLMInvoker.invoke(
        provider=provider,
        model_name=model_name,
        messages=[
            SystemMessage(content=REPAIR_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ],
        temperature=0.1
    )

    raw_patch = response.content

    print(
        f"\n================ LLM PATCH RAW ================\n"
        f"{raw_patch}\n"
        f"========================================="
    )

    history = list(
        state.get("repair_history", [])
    )

    history.append(
        f"[LLM PATCH]\n"
        f"attempt={state.get('repair_attempts', 0)}\n"
        f"{raw_patch}"
    )

    updates = parse_patch_response(raw_patch)

    merged_repo_files = dict(state["repo_files"])
    merged_repo_files.update(updates)

    return {
        **state,
        "repo_files": merged_repo_files,
        "repair_history": history,

        # 唯一增加次数的位置
        "repair_attempts":
            state.get("repair_attempts", 0) + 1
    }
def repairability_gate_node(state: AgentState):
    print("\n🔍 [Repairability Gate] 检查当前问题是否可自动修复...")

    from src.quality.repairability_gate import RepairabilityGate

    gate = RepairabilityGate()

    repairable, reason, options, needs_decision = gate.check(state)

    if not repairable:
        print("❌ [RepairabilityGate] 当前约束下无法自动修复")
        print(f"原因: {reason}")

        if options:
            print("💡 建议用户选择：")
            for i, option in enumerate(options, 1):
                print(f"   {i}. {option}")

        # 写入历史
        history = list(
            state.get("repair_history", [])
        )

        history.append(
            "[RepairabilityGate]\n"
            "UNREPAIRABLE_UNDER_CONSTRAINTS\n"
            f"reason={reason}"
        )

        return {
            **state,

            # 停止状态
            "repairable": False,
            "repair_status":
                "UNREPAIRABLE_UNDER_CONSTRAINTS",

            # 给 UI / 用户看的
            "repairability_reason": reason,
            "repair_options": options,
            "needs_user_decision":
                needs_decision,

            # 保持失败态
            "is_fixed": False,

            # 历史
            "repair_history": history,
        }

    print("✅ [RepairabilityGate] 当前仍可继续修复")
    print("\n[DEBUG] repair_attempts =", state.get("repair_attempts"))
    print("[DEBUG] sandbox_stderr exists =", bool(state.get("sandbox_stderr")))
    print("[DEBUG] semantic_gate_reason =", state.get("semantic_gate_reason"))
    print("[DEBUG] policy_gate_reason =", state.get("policy_gate_reason"))

    return {
        **state,
        "repairable": True,
        "repair_status": "REPAIRABLE",
        "repairability_reason": reason,
        "repair_options": options,
        "needs_user_decision":
            needs_decision,
    }
# =========================================================
# semantic_patch_gate_node
# 唯一变化：透传 sandbox_stderr 给 SemanticPatchGate.check()
# =========================================================
def semantic_patch_gate_node(state: AgentState):
    print("\n🧠 [Semantic Patch Gate] 正在检查语义补丁质量...")

    gate = SemanticPatchGate()

    passed, reason = gate.check(
        repo_files=state.get("repo_files", {}),
        original_repo_files=state.get(
            "original_repo_files",
            {}
        ),
        analysis=state.get("analysis", ""),
        target_files=state.get(
            "target_files",
            []
        ),
        sandbox_stderr=state.get(
            "sandbox_stderr",
            ""
        ),
    )

    history = list(
        state.get("repair_history", [])
    )

    if passed:
        print("✅ [Semantic Patch Gate] 检查通过")

    else:
        print("❌ [Semantic Patch Gate] 检查失败")
        print(f"原因: {reason}")

        history.append(
            "[Semantic Patch Failure]\n"
            f"reason={reason}\n"
            f"repair_attempts="
            f"{state.get('repair_attempts', 0)}"
        )

    # 注意：
    # Semantic Gate 不再修改 repair_attempts
    # repair_attempts ONLY 在 repair_node 中 +1

    return {
        **state,
        "semantic_gate_passed": passed,
        "semantic_gate_reason": reason,
        "repair_history": history,
    }
# =========================================================
# Verify Node
# =========================================================
def verify_node(state: AgentState):
    print("🧪 [Verify] 正在进行沙箱验证...")
    executor = CodeExecutor(repo_root=state["repo_root"])
    success, error_log, stdout, stderr = executor.run_v3_validation(state["repo_files"])

    if success:
        print("🎉 所有测试通过")
    else:
        print("❌ 沙箱验证失败")

    return {
        **state,
        "is_fixed": success,
        "error_message": error_log,
        "sandbox_stdout": stdout,
        "sandbox_stderr": stderr
    }
# =========================================================
# Patch Quality Gate Node
# =========================================================
def patch_quality_gate_node(state: AgentState):
    print("\n🧪 [Patch Quality Gate] 正在检查补丁质量...")

    gate = PatchQualityGate()

    passed, reason = gate.check(
        analysis=state.get("analysis", ""),
        original_files=state.get(
            "original_repo_files",
            {}
        ),
        repaired_files=state.get(
            "repo_files",
            {}
        ),
        target_files=state.get(
            "target_files",
            []
        )
    )

    history = list(
        state.get("repair_history", [])
    )

    if not passed:
        print(
            f"❌ [Patch Quality Gate] 检查失败: {reason}"
        )

        history.append(
            "[Patch Gate Failure]\n"
            f"reason={reason}\n"
            f"repair_attempts="
            f"{state.get('repair_attempts', 0)}"
        )

    else:
        print("✅ [Patch Quality Gate] 检查通过")

    # 注意：
    # 不再增加 repair_attempts
    # repair_attempts ONLY 在 repair_node 中 +1

    return {
        **state,
        "patch_quality_passed": passed,
        "patch_quality_reason": reason,
        "repair_history": history
    }
# =========================================================
# Continue Router
# =========================================================
def should_continue(state):

    if state.get("is_fixed"):
        return END

    repair_attempts = state.get(
        "repair_attempts",
        0
    )

    if repair_attempts >= 5:
        print(
            "\n🚨 达到最大修复轮次"
        )
        return END

    return "diagnose"

def should_continue_after_patch_gate(state: AgentState):
    if state.get("patch_quality_passed", False):
        print("✅ [Gate] Patch Quality 通过")
        return "semantic_patch_gate"
    
    repair_attempts = state.get("repair_attempts", 0)
    if repair_attempts >= 5:
        print("💀 Patch Gate 超过最大修复次数")
        return END
    return "repair"

def should_continue_after_semantic_gate(state: AgentState):
    if state.get("semantic_gate_passed", False):
        print("✅ [Gate] Semantic Patch 通过")
        return "verify"
    
    repair_attempts = state.get("repair_attempts", 0)
    if repair_attempts >= 5:
        print("💀 Semantic Gate 超过最大修复次数")
        return END
    return "repair"

def policy_gate_node(state: AgentState):
    print("\n🧠 [Policy Gate] 正在检查修复策略违规...")

    ok, reason = run_policy_gate(
        state["original_repo_files"],
        state["repo_files"]
    )

    if not ok:
        print(f"❌ [PolicyGate] 检查失败: {reason}")

        return {
            **state,
            "policy_gate_passed": False,
            "policy_gate_reason": reason
        }

    print("✅ [PolicyGate] 检查通过")
    print("✅ [Gate] Policy Gate 通过")

    return {
        **state,
        "policy_gate_passed": True,
        "policy_gate_reason": ""
    }


# ------------------------------------------------
# Repairability Router
# ------------------------------------------------
def should_continue_after_repairability(state):

    repairable = state.get(
        "repairable",
        True
    )

    print(
        f"\n[DEBUG] repairable = {repairable}"
    )

    if repairable:
        print(
            "🔁 [RepairabilityGate] 允许继续修复"
        )
        return "diagnose"

    print(
        "🛑 [RepairabilityGate] 已终止自动修复流程"
    )

    return "stop"


def create_v4_medic_graph():

    workflow = StateGraph(
        AgentState
    )

    # ---------------------------------
    # Nodes
    # ---------------------------------
    workflow.add_node(
        "diagnose",
        diagnose_node
    )

    workflow.add_node(
        "repair",
        repair_node
    )

    workflow.add_node(
        "patch_quality_gate",
        patch_quality_gate_node
    )

    workflow.add_node(
        "semantic_patch_gate",
        semantic_patch_gate_node
    )

    workflow.add_node(
        "policy_gate",
        policy_gate_node
    )

    workflow.add_node(
        "repairability_gate",
        repairability_gate_node
    )

    workflow.add_node(
        "verify",
        verify_node
    )

    # ---------------------------------
    # Base Flow
    # ---------------------------------
    workflow.add_edge(
        START,
        "diagnose"
    )

    workflow.add_edge(
        "diagnose",
        "repair"
    )

    workflow.add_edge(
        "repair",
        "patch_quality_gate"
    )

    # ---------------------------------
    # Patch Gate
    # ---------------------------------
    workflow.add_conditional_edges(
        "patch_quality_gate",
        should_continue_after_patch_gate,
        {
            "repair": "repair",
            "semantic_patch_gate":
                "semantic_patch_gate",
            END: END,
        }
    )

    # ---------------------------------
    # Semantic Gate
    # ---------------------------------
    workflow.add_conditional_edges(
        "semantic_patch_gate",
        should_continue_after_semantic_gate,
        {
            "repair": "repair",
            "verify": "policy_gate",
            END: END,
        }
    )

    # ---------------------------------
    # Policy Gate
    # ---------------------------------
    workflow.add_conditional_edges(
        "policy_gate",
        lambda s:
            "verify"
            if s.get(
                "policy_gate_passed",
                False
            )
            else "repairability_gate",
        {
            "verify": "verify",
            "repairability_gate":
                "repairability_gate",
        }
    )

    # ---------------------------------
    # Verify -> Repairability Gate
    # ---------------------------------
    workflow.add_edge(
        "verify",
        "repairability_gate"
    )

    # ---------------------------------
    # Repairability Gate
    # repairable=True  -> diagnose
    # repairable=False -> END
    # ---------------------------------
    workflow.add_conditional_edges(
        "repairability_gate",
        should_continue_after_repairability,
        {
            "diagnose":
                "diagnose",

            "stop":
                END,
        }
    )

    return workflow.compile()
