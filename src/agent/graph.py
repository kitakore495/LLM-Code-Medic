import os
import re

from dotenv import load_dotenv

from typing import TypedDict
from typing import List
from typing import Dict

from langgraph.graph import (
    StateGraph,
    START,
    END
)

from langchain_openai import ChatOpenAI
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

    # ======================================================
    # DeepSeek
    # ======================================================
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
            api_key=api_key,
            base_url=api_base,
            temperature=temperature
        )

    # ======================================================
    # Gemini（懒加载）
    # ======================================================
    elif provider == "gemini":

        try:
            from langchain_google_genai import (
                ChatGoogleGenerativeAI
            )

        except ImportError:
            raise RuntimeError(
                "\n缺少 Gemini SDK。\n"
                "请执行：\n\n"
                "pip install langchain-google-genai\n"
            )

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:
            raise RuntimeError(
                "缺少 GEMINI_API_KEY"
            )

        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature
        )

    # ======================================================
    # Unknown Provider
    # ======================================================
    raise RuntimeError(
        f"未知 provider: {provider}"
    )


# =========================================================
# Diagnose Node
# =========================================================
def diagnose_node(
    state: AgentState
):

    attempt = state["attempts"] + 1

    print(
        f"\n🚀 [Diagnose] "
        f"第 {attempt} 轮诊断..."
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

    repo_context = ""

    for path, content in state[
        "repo_files"
    ].items():

        repo_context += (
            f"\n===== FILE: "
            f"{path} =====\n"
        )

        repo_context += content
        repo_context += "\n"

    human_prompt = f"""
【AST 全景地图】

{state["project_map"]}

【项目源码快照】

{repo_context}

【当前错误】

{state["error_message"]}
""".strip()

    response = llm.invoke([
        SystemMessage(
            content=DIAGNOSE_SYSTEM_PROMPT
        ),
        HumanMessage(
            content=human_prompt
        )
    ])

    analysis = response.content

    # ======================================================
    # TARGET_FILES parser
    # ======================================================
    target_files = []

    match = re.search(
        r"TARGET_FILES:\s*\[(.*?)\]",
        analysis,
        re.DOTALL
    )

    if match:

        raw_files = match.group(1)

        files = re.findall(
            r"'(.*?)'|\"(.*?)\"",
            raw_files
        )

        parsed_files = []

        for item in files:

            path = item[0] or item[1]

            path = (
                path
                .replace("\\", "/")
                .strip()
            )

            # 去掉错误前缀
            path = re.sub(
                r"^(tests/v\d+/)",
                "",
                path
            )

            path = re.sub(
                r"^(v\d+/)",
                "",
                path
            )

            if path:
                parsed_files.append(
                    path
                )

        target_files = list(
            dict.fromkeys(
                parsed_files
            )
        )

    print(
        f"🎯 目标文件: "
        f"{target_files}"
    )

    return {
        **state,
        "attempts": attempt,
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

    repo_context = ""

    for path, content in state[
        "repo_files"
    ].items():

        repo_context += (
            f"\n===== FILE: "
            f"{path} =====\n"
        )

        repo_context += content
        repo_context += "\n"

    prompt = f"""
【错误分析】

{state["analysis"]}

【目标文件】

{state["target_files"]}

【当前仓库代码】

{repo_context}
""".strip()

    response = llm.invoke([
        SystemMessage(
            content=REPAIR_SYSTEM_PROMPT
        ),
        HumanMessage(
            content=prompt
        )
    ])

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

    # ======================================================
    # Patch parser
    # ======================================================
    patch_pattern = re.findall(
        r"<<<FILE_PATH:\s*(.*?)>>>"
        r"\n(.*?)"
        r"<<<FILE_END>>>",
        raw_patch,
        re.DOTALL
    )

    print(
        f"\n📝 已解析补丁块数量: "
        f"{len(patch_pattern)}"
    )

    for path, content in patch_pattern:

        path = (
            path
            .replace("\\", "/")
            .strip()
        )

        path = re.sub(
            r"^(tests/v\d+/)",
            "",
            path
        )

        path = re.sub(
            r"^(v\d+/)",
            "",
            path
        )

        repo_files[path] = (
            content.strip()
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
        repo_root=state[
            "repo_root"
        ]
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

    else:

        print(
            "❌ 沙箱验证失败"
        )

    return {
        **state,
        "is_fixed": success,
        "error_message": error_message
    }


# =========================================================
# Router
# =========================================================
def route_after_verify(
    state: AgentState
):

    if state["is_fixed"]:
        return END

    if state["attempts"] >= 3:
        return END

    return "diagnose"


# =========================================================
# Build Graph
# =========================================================
def create_v4_medic_graph():

    workflow = StateGraph(
        AgentState
    )

    workflow.add_node(
        "diagnose",
        diagnose_node
    )

    workflow.add_node(
        "repair",
        repair_node
    )

    workflow.add_node(
        "verify",
        verify_node
    )

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
        "verify"
    )

    workflow.add_conditional_edges(
        "verify",
        route_after_verify
    )

    return workflow.compile()