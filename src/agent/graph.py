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
def diagnose_node(state: AgentState):
    print(f"\n🚀 [Diagnose] 第 {state.get('attempts', 0) + 1} 轮诊断...")

    provider, model_name = create_diagnose_llm()

    repo_snapshot_text = "\n".join(
        [f"\n===== FILE: {path} =====\n{code}" for path, code in state["repo_files"].items()]
    )
    repair_history_text = "\n\n".join(state.get("repair_history", []))

    user_prompt = f"""
请修复当前项目。

========================
【根因分析】
========================
{state.get("analysis", "首次诊断")}

========================
【需要修复的源码】
========================
{repo_snapshot_text}

========================
【Patch Gate Failure】
========================
{state.get("patch_quality_reason", "")}

========================
【Semantic Gate Failure】
========================
{state.get("semantic_gate_reason", "")}

========================
【历史失败修复】
========================
{repair_history_text}

========================
【最近一次 stderr】
========================
{state.get("sandbox_stderr", "")}

========================
【最高优先级指令】
========================
1. 严格按照 DIAGNOSE_SYSTEM_PROMPT 中的 TRACEBACK REASONING 和 ROOT_CAUSE_CLASS 进行根因分类。
2. 准确判断是 [CONTRACT_UNDEFINED] 还是 [CALLER_VIOLATED]。
3. 如果是 [CALLER_VIOLATED]，优先建议修复调用方传入的参数，使其符合被调用方的业务契约。
4. 必须输出 TARGET_FILES 列表，列出真正需要修改的文件。
5. 最终目标是让程序完整执行业务流程并输出正确结果，而非仅仅捕获异常或添加防御代码。

严格按照 DIAGNOSE_SYSTEM_PROMPT 输出格式。
""".strip()

    response = LLMInvoker.invoke(
        provider=provider,
        model_name=model_name,
        messages=[
            SystemMessage(content=DIAGNOSE_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ],
        temperature=0.1
    )

    analysis = response.content

    # ==================== TARGET_FILES 解析 ====================
    target_files = []
    files_match = re.search(r"TARGET_FILES:\s*(\[.*?\])", analysis, re.DOTALL | re.IGNORECASE)
    if files_match:
        try:
            import json
            normalized = files_match.group(1).replace("'", '"')
            parsed = json.loads(normalized)
            if isinstance(parsed, list):
                target_files = [p.strip() for p in parsed if isinstance(p, str)]
        except Exception:
            pass

    # 路径清洗 + 兜底
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
        "attempts": state.get("attempts", 0) + 1
    }
# =========================================================
# Repair Node
# =========================================================
def repair_node(state: AgentState):
    print("🛠️ [Repair] 正在生成多文件补丁...")

    provider, model_name = create_repair_llm()

    repo_snapshot_text = "\n".join(
        [f"\n===== FILE: {path} =====\n{code}" 
         for path, code in state["repo_files"].items() 
         if not state.get("target_files") or path in state.get("target_files")]
    )

    repair_history_text = "\n\n".join(state.get("repair_history", []))

    user_prompt = f"""
请修复当前项目。

【根因分析】
{state.get("analysis", "未提供根因分析")}

【需要修复的源码】
{repo_snapshot_text}

【Semantic Gate Failure】
{state.get("semantic_gate_reason", "")}

【历史失败修复】
{repair_history_text}

【最高优先级修复策略】
1. 严格根据【根因分析】中的 ROOT_CAUSE_CLASS 和 REPAIR_SCOPE 执行修复。
2. 如果诊断结果为 [CALLER_VIOLATED]，则优先在调用方修正参数，使其符合业务契约。
3. 必须使用命名常量表示业务阈值，严禁直接使用魔法数字。
4. 禁止仅在被调用方增加防御性代码而不修复调用方的根本问题。
5. 禁止添加 try-except 来吞噬业务异常。
6. 最终目标是让程序完整执行业务流程并成功输出预期结果。

严格遵守 REPAIR_SYSTEM_PROMPT 中的 SELF_VERIFICATION 要求。
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
    print(f"\n================ LLM PATCH RAW ================\n{raw_patch}\n=========================================")

    history = state.get("repair_history", [])
    history.append(f"[LLM PATCH] attempt: {state.get('repair_attempts', 0)}\n{raw_patch}")

    updates = parse_patch_response(raw_patch)
    merged_repo_files = dict(state["repo_files"])
    merged_repo_files.update(updates)

    return {
        **state,
        "repo_files": merged_repo_files,
        "repair_history": history,
        "repair_attempts": state.get("repair_attempts", 0) + 1
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
        original_files=state.get("original_repo_files", {}),
        repaired_files=state.get("repo_files", {}),
        target_files=state.get("target_files", [])
    )

    if not passed:
        print(f"❌ [Patch Quality Gate] 检查失败: {reason}")
        history = state.get("repair_history", [])
        history.append(f"[Patch Gate Failure] {reason}")
        state["repair_history"] = history
        state["repair_attempts"] = state.get("repair_attempts", 0) + 1
    else:
        print("✅ [Patch Quality Gate] 检查通过")

    return {
        **state,
        "patch_quality_passed": passed,
        "patch_quality_reason": reason
    }
# =========================================================
# Semantic Patch Gate Node
# =========================================================
def semantic_patch_gate_node(state: AgentState):
    print("\n🧠 [Semantic Patch Gate] 正在检查语义补丁质量...")
    gate = SemanticPatchGate()
    passed, reason = gate.check(
        repo_files=state.get("repo_files", {}),
        original_repo_files=state.get("original_repo_files", {}),
        analysis=state.get("analysis", ""),
        target_files=state.get("target_files", [])
    )

    if not passed:
        print(f"❌ [Semantic Patch Gate] 检查失败: {reason}")
        # 记录失败历史（修复 Bug 3）
        history = state.get("repair_history", [])
        history.append(f"[Semantic Patch Failure] reason: {reason}")
        state["repair_history"] = history
        state["repair_attempts"] = state.get("repair_attempts", 0) + 1

    return {
        **state,
        "semantic_gate_passed": passed,
        "semantic_gate_reason": reason
    }
# =========================================================
# Continue Router
# =========================================================
def should_continue(state: AgentState):
    if state.get("is_fixed"):
        return END
    if state.get("attempts", 0) >= 5:
        print("\n🚨 达到最大修复轮次")
        return END
    return "diagnose"

def should_continue_after_patch_gate(state: AgentState):
    if state.get("patch_quality_passed", False):
        print("✅ [Gate] Patch Quality 通过")
        return "semantic_patch_gate"
    
    attempts = state.get("repair_attempts", 0)
    if attempts >= 5:
        print("💀 Patch Gate 超过最大修复次数")
        return END
    return "repair"

def should_continue_after_semantic_gate(state: AgentState):
    if state.get("semantic_gate_passed", False):
        print("✅ [Gate] Semantic Patch 通过")
        return "verify"
    
    attempts = state.get("repair_attempts", 0)
    if attempts >= 5:
        print("💀 Semantic Gate 超过最大修复次数")
        return END
    return "repair"
# =========================================================
# Build Graph
# =========================================================
def create_v4_medic_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("diagnose", diagnose_node)
    workflow.add_node("repair", repair_node)
    workflow.add_node("patch_quality_gate", patch_quality_gate_node)
    workflow.add_node("semantic_patch_gate", semantic_patch_gate_node)
    workflow.add_node("verify", verify_node)

    workflow.add_edge(START, "diagnose")
    workflow.add_edge("diagnose", "repair")
    workflow.add_edge("repair", "patch_quality_gate")

    workflow.add_conditional_edges(
        "patch_quality_gate",
        should_continue_after_patch_gate,
        {
            "repair": "repair",
            "semantic_patch_gate": "semantic_patch_gate",
            END: END,
            "__end__": END
        }
    )

    workflow.add_conditional_edges(
        "semantic_patch_gate",
        should_continue_after_semantic_gate,
        {
            "repair": "repair",
            "verify": "verify",
            END: END,
            "__end__": END
        }
    )

    workflow.add_conditional_edges("verify", should_continue)

    return workflow.compile()