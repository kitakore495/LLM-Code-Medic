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
    get_diagnose_llm,
    get_repair_llm
)


# =========================================================
# 状态结构
# =========================================================
class AgentState(TypedDict):
    repo_root: str
    project_map: str
    error_message: str
    target_files: List[str]
    repo_files: Dict[str, str]
    attempts: int
    is_fixed: bool
    analysis: str


# =========================================================
# Diagnose Node
# =========================================================
def diagnose_node(
    state: AgentState
):

    print(
        f"\n🚀 [Diagnose] "
        f"第 {state['attempts'] + 1} 轮诊断..."
    )

    llm = get_diagnose_llm()

    repo_context = ""

    for path, content in state[
        "repo_files"
    ].items():

        repo_context += (
            f"\n\n"
            f"===== FILE: {path} =====\n"
            f"{content}"
        )

    user_prompt = f"""
【AST 全景地图】
{state["project_map"]}

【项目源码快照】
{repo_context}

【错误日志】
{state["error_message"]}
""".strip()

    response = llm.invoke([

        SystemMessage(
            content=DIAGNOSE_SYSTEM_PROMPT
        ),

        HumanMessage(
            content=user_prompt
        )
    ])

    analysis = response.content

    match = re.search(
        r"TARGET_FILES:\s*(\[.*?\])",
        analysis,
        re.DOTALL
    )

    target_files = []

    if match:

        try:

            raw_files = eval(
                match.group(1)
            )

            for path in raw_files:

                clean_path = (
                    path
                    .replace("\\", "/")
                    .strip()
                )

                clean_path = re.sub(
                    r"^(tests/.*?/)",
                    "",
                    clean_path
                )

                clean_path = re.sub(
                    r"^(v\d+/)",
                    "",
                    clean_path
                )

                if clean_path in state[
                    "repo_files"
                ]:

                    target_files.append(
                        clean_path
                    )

        except Exception:

            pass

    # fallback
    if not target_files:
        target_files = list(
            state["repo_files"].keys()
        )

    print(
        f"🎯 目标文件: "
        f"{target_files}"
    )

    return {
        **state,
        "analysis": analysis,
        "target_files": target_files
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

    llm = get_repair_llm()

    target_context = ""

    for file_path in state[
        "target_files"
    ]:

        code = state[
            "repo_files"
        ].get(file_path)

        if code:

            target_context += (
                f"\n\n"
                f"===== FILE: {file_path} =====\n"
                f"{code}"
            )

    user_prompt = f"""
【错误分析】
{state["analysis"]}

【待修复文件源码】
{target_context}

请返回修复后的完整文件。
""".strip()

    response = llm.invoke([

        SystemMessage(
            content=REPAIR_SYSTEM_PROMPT
        ),

        HumanMessage(
            content=user_prompt
        )
    ])

    patch_text = response.content

    print(
        "\n================ "
        "LLM PATCH RAW "
        "================"
    )

    print(patch_text)

    print(
        "========================================="
    )

    pattern = re.compile(
        r"<<<FILE_PATH:\s*(.*?)>>>"
        r"\s*(.*?)"
        r"<<<FILE_END>>>",
        re.DOTALL
    )

    matches = pattern.findall(
        patch_text
    )

    print(
        f"\n📝 已解析补丁块数量: "
        f"{len(matches)}"
    )

    updated_repo_files = dict(
        state["repo_files"]
    )

    for file_path, code in matches:

        clean_path = (
            file_path
            .replace("\\", "/")
            .strip()
        )

        clean_path = re.sub(
            r"^(tests/.*?/)",
            "",
            clean_path
        )

        clean_path = re.sub(
            r"^(v\d+/)",
            "",
            clean_path
        )

        if clean_path in updated_repo_files:

            updated_repo_files[
                clean_path
            ] = code.strip()

            print(
                f"   -> 已更新: "
                f"{clean_path} "
                f"({len(code)} bytes)"
            )

    return {
        **state,
        "repo_files": updated_repo_files
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

    executor = CodeExecutor(
        state["repo_root"]
    )

    success, error_log = (
        executor.run_v3_validation(
            state["repo_files"]
        )
    )

    if success:

        print(
            "🎉 所有测试通过"
        )

        return {
            **state,
            "is_fixed": True
        }

    print(
        "❌ 沙箱验证失败"
    )

    return {
        **state,
        "attempts": state[
            "attempts"
        ] + 1,
        "error_message": error_log,
        "is_fixed": False
    }


# =========================================================
# Router
# =========================================================
def should_continue(
    state: AgentState
):

    if state["is_fixed"]:
        return END

    if state["attempts"] >= 3:
        return END

    return "diagnose"


# =========================================================
# Graph
# =========================================================
def create_v4_medic_graph():

    graph = StateGraph(
        AgentState
    )

    graph.add_node(
        "diagnose",
        diagnose_node
    )

    graph.add_node(
        "repair",
        repair_node
    )

    graph.add_node(
        "verify",
        verify_node
    )

    graph.add_edge(
        START,
        "diagnose"
    )

    graph.add_edge(
        "diagnose",
        "repair"
    )

    graph.add_edge(
        "repair",
        "verify"
    )

    graph.add_conditional_edges(
        "verify",
        should_continue
    )

    return graph.compile()