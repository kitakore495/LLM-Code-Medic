import os
import re

from dotenv import load_dotenv

# =========================================================
# 强制锁死加载 .env（兼容 Engine Core / VSCode / CLI）
# =========================================================
ROOT_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
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

from langchain_openai import (
    ChatOpenAI
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
# DeepSeek LLM 工厂
# =========================================================
def create_llm(model_name: str, temperature: float):

    api_key = os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("DEEPSEEK_API_BASE")

    if not api_key:
        raise RuntimeError("缺少 DEEPSEEK_API_KEY")

    if not base_url:
        raise RuntimeError("缺少 DEEPSEEK_API_BASE")

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=api_key,
        base_url=base_url
    )


# =========================================================
# 路径归一化（核心修复）
# =========================================================
def normalize_relative_path(path: str):

    path = path.strip()

    # windows -> unix
    path = path.replace("\\", "/")

    # 去掉 markdown 垃圾
    path = path.replace("`", "")

    # 去掉 ./ 开头
    path = re.sub(r"^\./", "", path)

    # 去掉 tests/v3/
    path = re.sub(r"^tests?/v3/", "", path)

    # 去掉 v3/
    path = re.sub(r"^v3/", "", path)

    # 去掉 output/
    path = re.sub(r"^output/", "", path)

    # 去掉 src/
    path = re.sub(r"^src/", "", path)

    # 防止重复斜杠
    path = re.sub(r"/+", "/", path)

    return path.strip("/")


# =========================================================
# 提取 TARGET_FILES
# =========================================================
def extract_target_files(text: str) -> List[str]:

    match = re.search(
        r"TARGET_FILES:\s*\[(.*?)\]",
        text,
        re.DOTALL
    )

    if not match:
        return []

    raw = match.group(1)

    result = []

    for item in raw.split(","):

        item = item.strip().strip("'\"")

        if not item:
            continue

        item = normalize_relative_path(item)

        result.append(item)

    return result


# =========================================================
# 解析多文件补丁
# =========================================================
def parse_patch_response(reply: str):

    pattern = re.compile(
        r"<<<FILE_PATH:\s*(.*?)\s*>>>\s*(.*?)\s*<<<FILE_END>>>",
        re.DOTALL
    )

    matches = pattern.findall(reply)

    cleaned_matches = []

    for file_path, code_content in matches:

        normalized_path = normalize_relative_path(
            file_path
        )

        cleaned_matches.append(
            (normalized_path, code_content)
        )

    return cleaned_matches


# =========================================================
# 清理 markdown codeblock
# =========================================================
def clean_code_block(content: str):

    content = content.strip()

    content = re.sub(
        r"^```(?:python)?",
        "",
        content
    )

    content = re.sub(
        r"```$",
        "",
        content
    )

    return content.strip()


# =========================================================
# Diagnose
# =========================================================
def diagnose_node(state: AgentState):

    print(
        f"\n🚀 [Diagnose] "
        f"第 {state['attempts'] + 1} 轮诊断..."
    )

    llm = create_llm(
        model_name="deepseek-ai/DeepSeek-R1",
        temperature=0.2
    )

    current_codes_context = "\n".join([
        f"--- 文件路径: {path} ---\n{content}\n"
        for path, content in state["repo_files"].items()
    ])

    user_content = f"""
【AST 全景地图】
{state['project_map']}

【仓库代码快照】
{current_codes_context}

【最新报错】
{state['error_message']}
"""

    messages = [
        SystemMessage(content=DIAGNOSE_SYSTEM_PROMPT),
        HumanMessage(content=user_content)
    ]

    response = llm.invoke(messages)

    analysis_text = response.content

    target_files = extract_target_files(
        analysis_text
    )

    if not target_files:

        print(
            "⚠️ 未提取到 TARGET_FILES，"
            "回退全仓修复"
        )

        target_files = list(
            state["repo_files"].keys()
        )

    print(f"🎯 目标文件: {target_files}")

    return {
        "analysis": analysis_text,
        "target_files": target_files,
        "attempts": state["attempts"] + 1
    }


# =========================================================
# Repair
# =========================================================
def repair_node(state: AgentState):

    print(
        "🛠️ [Repair] "
        "正在生成多文件补丁..."
    )

    llm = create_llm(
        model_name="deepseek-ai/DeepSeek-V3",
        temperature=0.1
    )

    user_content = f"""
【诊断报告】
{state['analysis']}

【必须修改的文件】
{state['target_files']}

【当前仓库代码】
{state['repo_files']}

请严格按照协议输出完整补丁。
"""

    messages = [
        SystemMessage(content=REPAIR_SYSTEM_PROMPT),
        HumanMessage(content=user_content)
    ]

    response = llm.invoke(messages)

    reply = response.content

    matches = parse_patch_response(reply)

    updated_repo_files = state["repo_files"].copy()

    if not matches:

        print("⚠️ 未解析到补丁")

        return {
            "repo_files": updated_repo_files
        }

    print(
        f"📝 已解析补丁块数量: "
        f"{len(matches)}"
    )

    for file_path, code_content in matches:

        normalized_path = normalize_relative_path(
            file_path
        )

        clean_code = clean_code_block(
            code_content
        )

        if not clean_code.strip():

            print(
                f"⚠️ 空补丁已跳过: "
                f"{normalized_path}"
            )

            continue

        updated_repo_files[
            normalized_path
        ] = clean_code

        print(
            f"   -> 已更新: "
            f"{normalized_path} "
            f"({len(clean_code)} bytes)"
        )

    return {
        "repo_files": updated_repo_files
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
        repo_root=state["repo_root"]
    )

    success, current_error = executor.run_v3_validation(
        state["repo_files"]
    )

    if success:

        print("🎉 所有测试通过")

        return {
            "is_fixed": True,
            "error_message": ""
        }

    print("❌ 沙箱验证失败")

    return {
        "is_fixed": False,
        "error_message": current_error
    }


# =========================================================
# Router
# =========================================================
def should_continue(state: AgentState):

    if state["is_fixed"]:
        return END

    if state["attempts"] >= 3:

        print(
            "🚨 达到最大重试次数"
        )

        return END

    return "diagnose"


# =========================================================
# 创建状态图
# =========================================================
def create_v3_medic_graph():

    workflow = StateGraph(AgentState)

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
        should_continue,
        {
            "diagnose": "diagnose",
            END: END
        }
    )

    return workflow.compile()