import os
import re

from dotenv import load_dotenv

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

from langchain_openai import ChatOpenAI
from langchain_google_genai import (
    ChatGoogleGenerativeAI
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
# Provider Router
# =========================================================
def create_llm(
    provider: str,
    model_name: str,
    temperature: float = 0.2
):

    provider = provider.lower()

    if provider == "deepseek":

        api_key = os.getenv(
            "DEEPSEEK_API_KEY"
        )

        api_base = os.getenv(
            "DEEPSEEK_API_BASE"
        )

        if not api_key:
            raise RuntimeError(
                "缺少 DEEPSEEK_API_KEY"
            )

        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key,
            base_url=api_base
        )

    elif provider == "gemini":

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:
            raise RuntimeError(
                "缺少 GEMINI_API_KEY"
            )

        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=api_key
        )

    raise RuntimeError(
        f"未知 provider: {provider}"
    )


# =========================================================
# Diagnose
# =========================================================
def diagnose_node(state: AgentState):

    print(
        f"\n🚀 [Diagnose] "
        f"第 {state['attempts'] + 1} 轮诊断..."
    )

    provider = os.getenv(
        "DIAGNOSE_PROVIDER",
        "deepseek"
    )

    model = os.getenv(
        "DIAGNOSE_MODEL",
        "deepseek-ai/DeepSeek-R1"
    )

    llm = create_llm(
        provider=provider,
        model_name=model,
        temperature=0.2
    )

    repo_snapshot = "\n\n".join(
        [
            f"===== {path} =====\n{code}"
            for path, code
            in state["repo_files"].items()
        ]
    )

    user_prompt = f"""
AST 全景地图：

{state["project_map"]}

当前代码仓库：

{repo_snapshot}

当前错误：

{state["error_message"]}
""".strip()

    response = llm.invoke(
        [
            SystemMessage(
                content=DIAGNOSE_SYSTEM_PROMPT
            ),
            HumanMessage(
                content=user_prompt
            )
        ]
    )

    analysis_text = response.content

    target_files = []

    # =====================================================
    # 1. 新协议：
    #
    # TARGET_FILES:
    # main.py
    # utils.py
    # =====================================================
    block_match = re.search(
        r"TARGET_FILES:\s*(.+)",
        analysis_text,
        re.DOTALL
    )

    if block_match:

        lines = block_match.group(1)

        for line in lines.splitlines():

            line = line.strip()

            if not line:
                continue

            if line.startswith(
                "ANALYSIS"
            ):
                continue

            line = (
                line
                .replace("tests/v3/", "")
                .replace("v3/", "")
                .replace("./", "")
                .strip("'\" ")
            )

            if line.endswith(".py"):
                target_files.append(
                    line
                )

    # =====================================================
    # 2. 老协议兼容
    #
    # TARGET_FILES:
    # ['main.py', 'utils.py']
    # =====================================================
    if not target_files:

        old_match = re.search(
            r"TARGET_FILES.*?\[(.*?)\]",
            analysis_text,
            re.DOTALL
        )

        if old_match:

            raw = old_match.group(1)

            target_files = re.findall(
                r"[A-Za-z0-9_/\-.]+\.py",
                raw
            )

    # =====================================================
    # 3. Gemini fallback
    # =====================================================
    if not target_files:

        target_files = re.findall(
            r"[A-Za-z0-9_/\-.]+\.py",
            analysis_text
        )

    target_files = list(
        dict.fromkeys(
            [
                x
                .replace("tests/v3/", "")
                .replace("v3/", "")
                for x in target_files
            ]
        )
    )

    print(
        f"🎯 目标文件: "
        f"{target_files}"
    )

    return {
        **state,
        "analysis": analysis_text,
        "target_files": target_files
    }


# =========================================================
# Repair
# =========================================================
def repair_node(state: AgentState):

    print(
        "🛠️ [Repair] "
        "正在生成多文件补丁..."
    )

    provider = os.getenv(
        "REPAIR_PROVIDER",
        "deepseek"
    )

    model = os.getenv(
        "REPAIR_MODEL",
        "deepseek-ai/DeepSeek-V3"
    )

    llm = create_llm(
        provider=provider,
        model_name=model,
        temperature=0.2
    )

    repo_snapshot = "\n\n".join(
        [
            f"===== {path} =====\n{code}"
            for path, code
            in state["repo_files"].items()
        ]
    )

    user_prompt = f"""
错误分析：

{state["analysis"]}

当前仓库：

{repo_snapshot}
""".strip()

    response = llm.invoke(
        [
            SystemMessage(
                content=REPAIR_SYSTEM_PROMPT
            ),
            HumanMessage(
                content=user_prompt
            )
        ]
    )

    raw_patch = response.content

    print(
        "\n================ "
        "LLM PATCH RAW "
        "================"
    )

    print(raw_patch)

    print(
        "========================================="
    )

    repo_files = dict(
        state["repo_files"]
    )

    patch_regex = re.compile(
        r"""
<<<FILE_PATH:\s*(.*?)>>>
(.*?)
<<<FILE_END>>>
""",
        re.DOTALL | re.VERBOSE
    )

    patches = patch_regex.findall(
        raw_patch
    )

    print(
        f"\n📝 已解析补丁块数量: "
        f"{len(patches)}"
    )

    for path, content in patches:

        path = (
            path.strip()
            .replace("tests/v3/", "")
            .replace("v3/", "")
            .replace("./", "")
        )

        repo_files[path] = (
            content.strip()
            + "\n"
        )

        print(
            f"   -> 已更新: "
            f"{path} "
            f"({len(content)} bytes)"
        )

    return {
        **state,
        "repo_files": repo_files
    }


# =========================================================
# Verify
# =========================================================
def verify_node(state: AgentState):

    print(
        "🧪 [Verify] "
        "正在进行沙箱验证..."
    )

    executor = CodeExecutor(
        state["repo_root"]
    )

    success, error_message = (
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
        "attempts":
        state["attempts"] + 1,
        "error_message":
        error_message
    }


# =========================================================
# Router
# =========================================================
def router(state: AgentState):

    if state["is_fixed"]:
        return END

    if state["attempts"] >= 3:
        return END

    return "diagnose"


# =========================================================
# Graph Builder
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
        router
    )

    return graph.compile()