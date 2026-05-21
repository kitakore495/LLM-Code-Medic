# src/agent/graph.py
import os
import re
from typing import TypedDict, Dict, List, Annotated
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

# 从项目本地模块导入组件
from src.agent.prompts import DIAGNOSE_SYSTEM_PROMPT, REPAIR_SYSTEM_PROMPT
from src.tools.scanner import ProjectScanner
from src.tools.executor import CodeExecutor

# ==========================================
# 1. 定义 V3 多文件协同状态机数据结构
# ==========================================
class AgentState(TypedDict):
    repo_root: str                  # 测试仓库的物理根目录
    project_map: str                # AST 全景地图上下文
    error_message: str              # 当前最新的集成测试报错信息
    target_files: List[str]         # R1 诊断出本次需要连带修改的文件清单
    repo_files: Dict[str, str]      # 整个仓库所有相关文件的最新代码映射 {相对路径: 代码内容}
    attempts: int                   # 当前迭代重试次数
    is_fixed: bool                  # 全物理闭环是否成功通关
    analysis: str                   # R1 的根因分析思维链或文本

# ==========================================
# 2. 核心节点流转逻辑定义
# ==========================================

def diagnose_node(state: AgentState) -> Dict:
    """
    [诊断节点] 调度 DeepSeek-R1 进行慢思考，找出导致 Bug 的多文件根因。
    """
    print(f"\n🚀 [Node: 诊断中...] 正在进行第 {state['attempts'] + 1} 次多文件联动诊断...")
    
    # 🎯【核心修复】强行锁死 DeepSeek 凭证，不再受默认 OpenAI 占位符干扰
    llm = ChatOpenAI(
        model="Pro/deepseek-ai/DeepSeek-R1",
        temperature=0.2,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_API_BASE")
    )
    
    current_codes_context = "\n".join([
        f"--- 文件路径: {path} ---\n{content}\n" 
        for path, content in state["repo_files"].items()
    ])
    
    user_content = f"""
【当前测试仓库 AST 全景地图】:
{state['project_map']}

【当前仓库内各文件代码快照】:
{current_codes_context}

【全仓库联合测试最新报错 Traceback】:
{state['error_message']}

请帮我深度分析报错根因。并在输出的最后，明确列出你需要修改的文件相对路径清单，格式为: 
TARGET_FILES: [文件1, 文件2]
"""

    messages = [
        SystemMessage(content=DIAGNOSE_SYSTEM_PROMPT),
        HumanMessage(content=user_content)
    ]
    
    response = llm.invoke(messages)
    analysis_text = response.content
    
    # 使用正则表达式提取大模型指定的待修改文件清单
    target_files = []
    match = re.search(r"TARGET_FILES:\s*\[(.*?)\]", analysis_text)
    if match:
        target_files = [f.strip().strip("'\"") for f in match.group(1).split(",") if f.strip()]
    
    if not target_files:
        target_files = list(state["repo_files"].keys())

    print(f"🎯 [诊断完成] R1 锁定的联动修改目标文件: {target_files}")
    
    return {
        "analysis": analysis_text,
        "target_files": target_files,
        "attempts": state["attempts"] + 1
    }


def repair_node(state: AgentState) -> Dict:
    """
    [修复节点] 调度 DeepSeek V4 Flash 模块快速生成结构化多文件代码补丁。
    """
    print(f"🛠️ [Node: 修复中...] 正在针对目标文件生成联动补丁...")
    
    # 🎯【核心修复】同样锁死为当前的 DeepSeek 模型和变量通道
    llm = ChatOpenAI(
        model="deepseek-ai/DeepSeek-V4-Flash",
        temperature=0.1,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_API_BASE")
    )
    
    user_content = f"""
【R1 导师给出的根因诊断报告】:
{state['analysis']}

【你本次必须修改的文件清单】:
{state['target_files']}

请严格按照 V3 多文件协议协议，同时输出这些文件修改后的【全量内容】。
"""

    messages = [
        SystemMessage(content=REPAIR_SYSTEM_PROMPT),
        HumanMessage(content=user_content)
    ]
    
    response = llm.invoke(messages)
    reply = response.content
    
    pattern = r"<<<FILE_PATH:\s*(.*?)\s*>>>(.*?)(?=<<<FILE_END>>>)"
    matches = re.findall(pattern, reply, re.DOTALL)
    
    updated_repo_files = state["repo_files"].copy()
    
    if matches:
        print(f"📝 成功解析到大模型吐出的多文件补丁包：")
        for file_path, code_content in matches:
            file_path = file_path.strip()
            clean_code = code_content.strip()
            if clean_code.startswith("```python"):
                clean_code = clean_code[9:]
            if clean_code.endswith("```"):
                clean_code = clean_code[:-3]
            clean_code = clean_code.strip()
            
            updated_repo_files[file_path] = clean_code
            print(f"   -> 已在内存中装配补丁: {file_path} ({len(clean_code)} 字节)")
    else:
        print("⚠️ 警告: 未能通过强规则解析到结构化多文件补丁，保持原代码不变。")

    return {"repo_files": updated_repo_files}


def verify_node(state: AgentState) -> Dict:
    """
    [验证节点] 将内存中打好补丁的多文件全量写入物理磁盘，并调用沙箱进行全项目集成测试。
    """
    print(f"🧪 [Node: 验证中...] 开启多文件全项目集成编译与沙箱测试...")
    
    executor = CodeExecutor(repo_root=state["repo_root"])
    success, current_error = executor.run_v3_validation(state["repo_files"])
    
    if success:
        print("🎉【完美通关】全项目联合测试 100% 运行成功！Bug 已被彻底消灭！")
        return {"is_fixed": True, "error_message": ""}
    else:
        print(f"❌ 测试未通过，沙箱捕获到全新报错。已自动执行物理原子回滚。")
        return {"is_fixed": False, "error_message": current_error}

# ==========================================
# 3. 动态控制流转路由定义（有向图条件边）
# ==========================================
def should_continue(state: AgentState):
    if state["is_fixed"]:
        return END
    if state["attempts"] >= 3:
        print("\n🚨 [达最大重试上限] 连续 3 次多文件连环修复均未成功，策略中断，抱憾收工。")
        return END
    return "diagnose"

# ==========================================
# 4. 构建 LangGraph 状态机拓扑网络
# ==========================================
def create_v3_medic_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("diagnose", diagnose_node)
    workflow.add_node("repair", repair_node)
    workflow.add_node("verify", verify_node)
    
    workflow.add_edge(START, "diagnose")
    workflow.add_edge("diagnose", "repair")
    workflow.add_edge("repair", "verify")
    
    workflow.add_conditional_edges(
        "verify",
        should_continue,
        {
            "diagnose": "diagnose",
            END: END
        }
    )
    
    return workflow.compile()