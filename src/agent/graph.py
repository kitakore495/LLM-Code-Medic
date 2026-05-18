import os
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from src.tools.executor import CodeExecutor
from src.agent.prompts import DIAGNOSE_SYSTEM_PROMPT, REPAIR_SYSTEM_PROMPT

# 1. 定义 V2 增强版状态结构
class AgentState(TypedDict):
    code: str            # 待修复的代码
    error_message: str   # executor 捕获的报错
    analysis: str        # DeepSeek R1 的推理诊断报告
    project_map: str     # ✨ V2 新增：ProjectScanner 扫出的项目全局地图背景
    repo_root: str       # ✨ V2 新增：当前测试项目的根目录路径（用于跨文件执行环境切换）
    attempts: int        # 当前重试次数
    is_fixed: bool       # 是否修复成功的标志位

# 2. 模型加载工厂 (保持硅基流动 DeepSeek 配置)
def get_model(purpose: str):
    # 诊断节点推荐用 R1 (强推理、会查阅地图连线)；修复节点用 V4-Flash / V3 (生成稳且快)
    model_name = "Pro/deepseek-ai/DeepSeek-R1" if purpose == "diagnose" else "deepseek-ai/DeepSeek-V4-Flash"
    
    return ChatOpenAI(
        model=model_name,
        openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
        openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
        temperature=0.3 if purpose == "diagnose" else 0.7  # 诊断要求严谨，修复可以稍微灵活
    )

# --- 3. 智能体节点函数定义 ---

def diagnose_node(state: AgentState):
    print(f"🔎 [Node: Diagnose] 正在分析错误原因 (第 {state['attempts']+1} 次尝试)...")
    model = get_model("diagnose")
    
    # ✨ 将项目地图作为上文喂给 R1，引导它去比对跨文件引用
    prompt = (
        f"【项目目录结构地图】:\n{state['project_map']}\n\n"
        f"【当前报错文件的代码】:\n{state['code']}\n\n"
        f"【运行报错信息】:\n{state['error_message']}"
    )
    
    response = model.invoke([
        ("system", DIAGNOSE_SYSTEM_PROMPT),
        ("user", prompt)
    ])
    return {"analysis": response.content}

def repair_node(state: AgentState):
    print("🛠️ [Node: Repair] 正在生成修复方案...")
    model = get_model("repair")
    
    # ✨ 修复节点同样带上地图背景，防止 Flash 乱改或瞎编 import 路径
    prompt = (
        f"【项目目录结构地图】:\n{state['project_map']}\n\n"
        f"【原始代码】:\n{state['code']}\n\n"
        f"【诊断报告】:\n{state['analysis']}"
    )
    
    response = model.invoke([
        ("system", REPAIR_SYSTEM_PROMPT),
        ("user", prompt)
    ])
    # 严格清理 Markdown 标签
    new_code = response.content.replace("```python", "").replace("```", "").strip()
    return {"code": new_code}

def verify_node(state: AgentState):
    print("🧪 [Node: Verify] 正在执行代码验证...")
    executor = CodeExecutor()
    
    # ✨ V2 核心修正：运行验证时传入 repo_root，让执行器动态切换到 mock 文件夹下执行
    result = executor.run_code(state["code"], repo_root=state.get("repo_root"))
    
    if result["success"]:
        print("✅ 修复成功！代码已可以正常运行。")
        return {"is_fixed": True, "error_message": "", "attempts": state["attempts"] + 1}
    else:
        # ✨ 安全切片：防止 result["error"] 为空或无换行导致的 IndexError 崩溃
        error_lines = result["error"].splitlines() if result["error"] else []
        last_error = error_lines[-1] if error_lines else "Unknown Error"
        print(f"❌ 依然存在错误：{last_error}")
        return {"is_fixed": False, "error_message": result["error"], "attempts": state["attempts"] + 1}

# 4. 路由跳转控制
def decide_to_continue(state: AgentState):
    if state["is_fixed"]:
        return "end"
    if state["attempts"] >= 3:
        print("⚠️ 已达到最大重试次数，修复终止。")
        return "end"
    return "continue"

# 5. 组装 LangGraph 工作流图
workflow = StateGraph(AgentState)

workflow.add_node("diagnose", diagnose_node)
workflow.add_node("repair", repair_node)
workflow.add_node("verify", verify_node)

workflow.set_entry_point("diagnose")
workflow.add_edge("diagnose", "repair")
workflow.add_edge("repair", "verify")

workflow.add_conditional_edges(
    "verify",
    decide_to_continue,
    {
        "continue": "diagnose",
        "end": END
    }
)

app = workflow.compile()