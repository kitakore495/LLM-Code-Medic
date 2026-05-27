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

ENV_PATH = os.path.join(
    ROOT_DIR,
    ".env"
)

load_dotenv(
    dotenv_path=ENV_PATH,
    override=True
)

from typing import TypedDict
from typing import List
from typing import Dict

from src.agent.state import (
    AgentState
)

from langgraph.graph import (
    StateGraph,
    START,
    END
)

from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

from src.agent.prompts import (
    DIAGNOSE_SYSTEM_PROMPT,
    REPAIR_SYSTEM_PROMPT
)

from src.tools.executor import (
    CodeExecutor
)

from src.llm.provider_router import (
    ProviderRouter
)

from src.llm.llm_invoker import (
    LLMInvoker
)

from src.quality.patch_quality_gate import (
    PatchQualityGate
)

from src.quality.semantic_patch_gate import (
    SemanticPatchGate
)

# =========================================================
# PATCH PARSER
# =========================================================
def parse_patch_response(
    raw_text: str
):

    repo_updates = {}

    pattern = re.compile(
        r"<<<FILE_PATH:\s*(.*?)>>>"
        r"(.*?)"
        r"<<<FILE_END>>>",
        re.DOTALL
    )

    matches = pattern.findall(
        raw_text
    )

    print(
        f"\n📝 已解析补丁块数量: "
        f"{len(matches)}"
    )

    for (
        relative_path,
        code
    ) in matches:

        relative_path = (
            relative_path
            .strip()
        )

        relative_path = (
            relative_path
            .replace("\\", "/")
        )

        # 防御式路径修正
        relative_path = re.sub(
            r"^(tests/[^/]+/)",
            "",
            relative_path
        )

        relative_path = re.sub(
            r"^(v\d+/)",
            "",
            relative_path
        )

        repo_updates[
            relative_path
        ] = code.strip()

        print(
            f"   -> 已更新: "
            f"{relative_path} "
            f"({len(code)} bytes)"
        )

    return repo_updates

# =========================================================
# Diagnose Config
# =========================================================
def create_diagnose_llm():

    provider = (
        ProviderRouter
        .get_diagnose_provider()
    )

    model_name = (
        ProviderRouter
        .get_diagnose_model()
    )

    print(
        f"🧠 Diagnose Provider: "
        f"{provider}"
    )

    print(
        f"🧠 Diagnose Model: "
        f"{model_name}"
    )

    return (
        provider,
        model_name
    )
# =========================================================
# Repair Config
# =========================================================
def create_repair_llm():

    provider = (
        ProviderRouter
        .get_repair_provider()
    )

    model_name = (
        ProviderRouter
        .get_repair_model()
    )

    print(
        f"🧠 Repair Provider: "
        f"{provider}"
    )

    print(
        f"🧠 Repair Model: "
        f"{model_name}"
    )

    return (
        provider,
        model_name
    )
# =========================================================
# Diagnose Node
# =========================================================
def diagnose_node(
    state: AgentState
):

    print(
        f"\n🚀 [Diagnose] "
        f"第 {state['attempts'] + 1} "
        f"轮诊断..."
    )

    (
        provider,
        model_name
    ) = (
        create_diagnose_llm()
    )

    # =====================================================
    # Repo Snapshot
    # =====================================================
    repo_snapshot = []

    for (
        path,
        code
    ) in state[
        "repo_files"
    ].items():

        repo_snapshot.append(
            f"\n===== FILE: "
            f"{path} =====\n"
        )

        repo_snapshot.append(
            code
        )

    repo_snapshot_text = (
        "\n".join(
            repo_snapshot
        )
    )

    # =====================================================
    # Repair History
    # =====================================================
    repair_history_text = "\n\n".join(

        state.get(
            "repair_history",
            []
        )
    )

    # =====================================================
    # Prompt
    # =====================================================
    user_prompt = f"""
请分析当前软件项目。

【AST 全景地图】
{state["project_map"]}

【仓库源码快照】
{repo_snapshot_text}

【当前运行失败信息】
{state["error_message"]}

【Patch Gate Failure】
{state.get("patch_quality_reason", "")}

【Semantic Gate Failure】
{state.get("semantic_gate_reason", "")}

【历史失败修复】
{repair_history_text}

请进行：

慢思考根因诊断（Slow Thinking）。

要求：

1. 不要只修 traceback 最后一行
2. 不要重复失败 patch
3. 不要 workaround
4. 不要修改 magic number
5. 不要修改公式绕过问题
6. 必须关注 stdout 是否异常
7. 必须修复真实根因
8. 必须进行跨文件调用链分析
9. 必须进行 runtime 风险分析
10. 必须判断 previous repair 是否只是 workaround

特别注意：

程序“运行成功”
≠
修复成功。

stdout 异常：

依然属于失败。

如果 semantic gate 拒绝了 patch：

必须主动思考：

为什么被拒绝？

不能重复生成同类 patch。
""".strip()

    # =====================================================
    # LLM Diagnose
    # =====================================================
    response = (
        LLMInvoker
        .invoke(
            provider=provider,
            model_name=model_name,
            messages=[

                SystemMessage(
                    content=(
                        DIAGNOSE_SYSTEM_PROMPT
                    )
                ),

                HumanMessage(
                    content=user_prompt
                )
            ],
            temperature=0.2
        )
    )

    analysis = (
        response.content
    )

    # =====================================================
    # Parse TARGET_FILES
    # =====================================================
    target_files = []

    match = re.search(
        r"TARGET_FILES:\s*(\[.*?\])",
        analysis,
        re.DOTALL
    )

    if match:

        try:

            import ast

            target_files = (
                ast.literal_eval(
                    match.group(1)
                )
            )

        except Exception:

            target_files = []

    # =====================================================
    # Defensive Path Cleanup
    # =====================================================
    cleaned = []

    for path in target_files:

        path = (
            path
            .replace("\\", "/")
            .strip()
        )

        path = re.sub(
            r"^(tests/[^/]+/)",
            "",
            path
        )

        path = re.sub(
            r"^(v\d+/)",
            "",
            path
        )

        cleaned.append(
            path
        )

    target_files = list(
        dict.fromkeys(
            cleaned
        )
    )

    print(
        f"🎯 目标文件: "
        f"{target_files}"
    )

    return {

        **state,

        "analysis":
            analysis,

        "target_files":
            target_files,

        "attempts":
            state[
                "attempts"
            ] + 1
    }
# =========================================================
# Repair Node
# =========================================================
def repair_node(
    state: AgentState
):

    print(
        "🛠️ [Repair] "
        "正在生成多文件补丁..."
    )

    (
        provider,
        model_name
    ) = (
        create_repair_llm()
    )

    # =====================================================
    # Repo Snapshot
    # =====================================================
    repo_snapshot = []

    for (
        path,
        code
    ) in state[
        "repo_files"
    ].items():

        if (
            state[
                "target_files"
            ]
            and path not in
            state[
                "target_files"
            ]
        ):
            continue

        repo_snapshot.append(
            f"\n===== FILE: "
            f"{path} =====\n"
        )

        repo_snapshot.append(
            code
        )

    repo_snapshot_text = (
        "\n".join(
            repo_snapshot
        )
    )

    # =====================================================
    # Repair History
    # =====================================================
    repair_history_text = (
        "\n\n".join(
            state.get(
                "repair_history",
                []
            )
        )
    )

    # =====================================================
    # Prompt
    # =====================================================
    user_prompt = f"""
请修复当前项目。

【根因分析】
{state["analysis"]}

【需要修复的源码】
{repo_snapshot_text}

【Patch Gate Failure】
{state.get(
    "patch_quality_reason",
    ""
)}

【Semantic Gate Failure】
{state.get(
    "semantic_gate_reason",
    ""
)}

【历史失败修复】
{repair_history_text}

【最近一次 stdout】
{state.get(
    "sandbox_stdout",
    ""
)}

【最近一次 stderr】
{state.get(
    "sandbox_stderr",
    ""
)}

重要：

程序运行成功
≠
修复成功。

如果 semantic gate 拒绝：

你必须主动思考：

为什么失败？

禁止重复 patch。

禁止 workaround。

禁止 magic number 修复。

禁止公式修改。

禁止：

10 → 20

9 → 8

x / y

↓

x / (y + 1)

禁止：

except: pass

return True

return None

max()

min()

必须：

修复真实根因。

要求：

1. 输出完整文件
2. 仅修改必要文件
3. 严禁解释
4. 严格遵守 FILE_PATH 协议
5. 不允许重复历史失败 patch
""".strip()

    # =====================================================
    # LLM Repair
    # =====================================================
    response = (
        LLMInvoker
        .invoke(
            provider=provider,
            model_name=model_name,
            messages=[

                SystemMessage(
                    content=(
                        REPAIR_SYSTEM_PROMPT
                    )
                ),

                HumanMessage(
                    content=user_prompt
                )
            ],
            temperature=0.2
        )
    )

    raw_patch = (
        response.content
    )

    print(
        "\n================ "
        "LLM PATCH RAW "
        "================"
    )

    print(
        raw_patch
    )

    print(
        "========================================="
    )

    # =====================================================
    # Save History
    # =====================================================
    history = state.get(
        "repair_history",
        []
    )

    history.append(
        f"""
[LLM PATCH]

attempt:
{state.get(
    "repair_attempts",
    0
)}

patch:
{raw_patch}
""".strip()
    )

    # =====================================================
    # Parse Patch
    # =====================================================
    updates = (
        parse_patch_response(
            raw_patch
        )
    )

    merged_repo_files = dict(
        state[
            "repo_files"
        ]
    )

    merged_repo_files.update(
        updates
    )

    return {

        **state,

        "repo_files":
            merged_repo_files,

        "repair_history":
            history
    }
# =========================================================
# Verify Node
# =========================================================
def verify_node(
    state: AgentState
):

    print(
        "🧪 [Verify] "
        "正在进行沙箱验证..."
    )

    executor = (
        CodeExecutor(
            repo_root=state[
                "repo_root"
            ]
        )
    )

    (
        success,
        error_log,
        stdout,
        stderr
    ) = (
        executor.run_v3_validation(
            state[
                "repo_files"
            ]
        )
    )

    # =====================================================
    # Semantic Runtime Check
    # =====================================================
    suspicious = False
    suspicious_reason = ""

    stdout_lower = (
        stdout.lower()
        if stdout
        else ""
    )

    suspicious_patterns = [

        "159.0",

        "nan",

        "inf",

        "none",

        "true"
    ]

    for item in suspicious_patterns:

        if item in stdout_lower:

            suspicious = True

            suspicious_reason = (
                f"stdout "
                f"出现可疑输出: "
                f"{item}"
            )

            break

    # =====================================================
    # Fake Success
    # =====================================================
    if success and suspicious:

        print(
            "⚠️ [Verify] "
            "程序运行成功，"
            "但检测到可疑语义输出"
        )

        print(
            f"原因: "
            f"{suspicious_reason}"
        )

        return {

            **state,

            "is_fixed":
                False,

            "error_message":
                suspicious_reason,

            "sandbox_stdout":
                stdout,

            "sandbox_stderr":
                stderr
        }

    # =====================================================
    # Success
    # =====================================================
    if success:

        print(
            "🎉 所有测试通过"
        )

    else:

        print(
            "❌ 沙箱验证失败"
        )

    return {

        **state,

        "is_fixed":
            success,

        "error_message":
            error_log,

        "sandbox_stdout":
            stdout,

        "sandbox_stderr":
            stderr
    }
# =========================================================
# Patch Quality Gate Node
# =========================================================
def patch_quality_gate_node(
    state: AgentState
):

    print(
        "\n🧪 [Patch Quality Gate] "
        "正在检查补丁质量..."
    )

    gate = PatchQualityGate()

    passed, reason = (
        gate.check(
            analysis=state.get(
                "analysis",
                ""
            ),

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
    )

    if passed:

        print(
            "✅ [Patch Quality Gate] "
            "补丁质量检查通过"
        )

    else:

        print(
            "❌ [Patch Quality Gate] "
            f"检查失败: "
            f"{reason}"
        )

    return {

        **state,

        "patch_quality_passed":
            passed,

        "patch_quality_reason":
            reason
    }
# =========================================================
# Semantic Patch Gate Node
# =========================================================
def semantic_patch_gate_node(
    state: AgentState
):

    print(
        "\n🧠 [Semantic Patch Gate] "
        "正在检查语义补丁质量..."
    )

    gate = (
        SemanticPatchGate()
    )

    passed, reason = (
        gate.check(

            repo_files=state.get(
                "repo_files",
                {}
            ),

            original_repo_files=state.get(
                "original_repo_files",
                {}
            ),

            analysis=state.get(
                "analysis",
                ""
            ),

            target_files=state.get(
                "target_files",
                []
            )
        )
    )

    if passed:

        print(
            "✅ [Semantic Patch Gate] "
            "检查通过"
        )

    else:

        print(
            "❌ [Semantic Patch Gate] "
            "检查失败"
        )

        print(
            f"原因: {reason}"
        )

    return {

        **state,

        "semantic_gate_passed":
            passed,

        "semantic_gate_reason":
            reason
    }
# =========================================================
# Continue Router
# =========================================================
def should_continue(
    state: AgentState
):

    if state[
        "is_fixed"
    ]:

        return END

    if state[
        "attempts"
    ] >= 5:

        print(
            "\n🚨 达到最大修复轮次"
        )

        return END

    return "diagnose"
# =========================================================
# Patch Gate Route
# =========================================================
def should_continue_after_patch_gate(
    state: AgentState
):

    passed = state.get(
        "patch_quality_passed",
        False
    )

    if passed:

        print(
            "✅ [Gate] "
            "Patch Quality 通过"
        )

        return (
            "semantic_patch_gate"
        )

    # =====================================================
    # Retry Count
    # =====================================================
    attempts = state.get(
        "repair_attempts",
        0
    )

    attempts += 1

    state[
        "repair_attempts"
    ] = attempts

    print(
        "❌ [Gate] "
        "Patch Quality "
        "失败，重新修复"
    )

    print(
        f"🔁 当前重修次数: "
        f"{attempts}/5"
    )

    # =====================================================
    # Record Failure History
    # =====================================================
    history = state.get(
        "repair_history",
        []
    )

    history.append(
        f"""
[Patch Gate Failure]

attempt:
{attempts}

reason:
{state.get(
    "patch_quality_reason",
    ""
)}

analysis:
{state.get(
    "analysis",
    ""
)}
""".strip()
    )

    state[
        "repair_history"
    ] = history

    # =====================================================
    # Stop Condition
    # =====================================================
    if attempts >= 5:

        print(
            "💀 超过最大修复次数"
        )

        return "__end__"

    return "repair"


# =========================================================
# Semantic Patch Gate Route
# =========================================================
def should_continue_after_semantic_gate(
    state: AgentState
):

    passed = state.get(
        "semantic_gate_passed",
        False
    )

    # =====================================================
    # Passed
    # =====================================================
    if passed:

        print(
            "✅ [Gate] "
            "Semantic Patch "
            "通过"
        )

        return "verify"

    # =====================================================
    # Retry Count
    # =====================================================
    attempts = state.get(
        "repair_attempts",
        0
    )

    attempts += 1

    state[
        "repair_attempts"
    ] = attempts

    print(
        "❌ [Gate] "
        "Semantic Patch "
        "失败，重新修复"
    )

    print(
        f"🔁 当前重修次数: "
        f"{attempts}/5"
    )

    # =====================================================
    # Record Failure History
    # =====================================================
    history = state.get(
        "repair_history",
        []
    )

    history.append(
        f"""
[Semantic Patch Failure]

attempt:
{attempts}

reason:
{state.get(
    "semantic_gate_reason",
    ""
)}

analysis:
{state.get(
    "analysis",
    ""
)}

stdout:
{state.get(
    "sandbox_stdout",
    ""
)}

stderr:
{state.get(
    "sandbox_stderr",
    ""
)}
""".strip()
    )

    state[
        "repair_history"
    ] = history

    # =====================================================
    # Stop Condition
    # =====================================================
    if attempts >= 5:

        print(
            "💀 超过最大修复次数"
        )

        return "__end__"

    return "repair"
# =========================================================
# Build Graph
# =========================================================
def create_v4_medic_graph():

    workflow = StateGraph(
        AgentState
    )

    # =====================================================
    # Nodes
    # =====================================================
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
        "verify",
        verify_node
    )

    # =====================================================
    # Flow
    # =====================================================
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

    # =====================================================
    # Patch Quality Gate
    # =====================================================
    workflow.add_conditional_edges(
        "patch_quality_gate",
        should_continue_after_patch_gate,
        {
            "repair": "repair",
            "semantic_patch_gate":
                "semantic_patch_gate"
        }
    )

    # =====================================================
    # Semantic Patch Gate
    # =====================================================
    workflow.add_conditional_edges(
        "semantic_patch_gate",
        should_continue_after_semantic_gate,
        {
            "repair": "repair",
            "verify": "verify"
        }
    )

    # =====================================================
    # Verify
    # =====================================================
    workflow.add_conditional_edges(
        "verify",
        should_continue
    )

    return workflow.compile()