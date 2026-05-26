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
# 状态结构
# =========================================================
class AgentState(TypedDict):

    repo_root: str

    project_map: str

    error_message: str

    target_files: List[
        str
    ]

    repo_files: Dict[
        str,
        str
    ]

    attempts: int

    is_fixed: bool

    analysis: str

    # =====================================================
    # Sandbox
    # =====================================================
    sandbox_stdout: str
    sandbox_stderr: str

    # =====================================================
    # Patch Quality Gate
    # =====================================================
    patch_quality_passed: bool
    patch_quality_reason: str

    # =====================================================
    # Semantic Patch Gate
    # =====================================================
    semantic_gate_passed: bool
    semantic_gate_reason: str


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

    user_prompt = f"""
请分析当前软件项目：

【AST 全景地图】
{state["project_map"]}

【仓库源码快照】
{repo_snapshot_text}

【当前错误】
{state["error_message"]}

请进行根因诊断。
""".strip()

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

    # 防御式路径清洗
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

    user_prompt = f"""
请修复当前项目。

【根因分析】
{state["analysis"]}

【需要修复的源码】
{repo_snapshot_text}

要求：

1. 输出完整文件
2. 仅修改必要文件
3. 不允许解释
4. 严格遵守 FILE_PATH 协议
""".strip()

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
        "repo_files":
            merged_repo_files
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

    success, error_log = (
        executor
        .run_v3_validation(
            state[
                "repo_files"
            ]
        )
    )

    if success:

        print(
            "🎉 所有测试通过"
        )

    else:

        print(
            "❌ 沙箱验证失败"
        )

    return {

        "is_fixed":
            success,

        "error_message":
            error_log
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

    repo_files = state[
        "repo_files"
    ]

    analysis = state.get(
        "analysis",
        ""
    )

    gate = PatchQualityGate()

    passed, reason = (
        gate.check(
            analysis=analysis,

            # 如果暂时没有初始快照
            original_files={},

            repaired_files=repo_files,

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

    result = (
        SemanticPatchGate
        .evaluate(
            repo_files=state[
                "repo_files"
            ],

            analysis=state.get(
                "analysis",
                ""
            ),

            patch=state.get(
                "patch",
                ""
            )
        )
    )

    passed = (
        result[
            "passed"
        ]
    )

    reason = (
        result[
            "reason"
        ]
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

    print(
        "❌ [Gate] "
        "Patch Quality "
        "失败，重新修复"
    )

    return "repair"
# =========================================================
# Continue After Semantic Gate
# =========================================================
def should_continue_after_semantic_gate(
    state: AgentState
):

    if state.get(
        "semantic_gate_passed",
        False
    ):

        print(
            "✅ [Gate] "
            "Semantic Patch "
            "通过"
        )

        return "verify"

    print(
        "❌ [Gate] "
        "Semantic Patch "
        "失败，重新修复"
    )

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