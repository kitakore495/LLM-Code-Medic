import os
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
# from langchain_google_genai import ChatGoogleGenerativeAI

from src.tools.executor import CodeExecutor
from src.agent.prompts import DIAGNOSE_SYSTEM_PROMPT, REPAIR_SYSTEM_PROMPT

# 1. 定义状态结构
class AgentState(TypedDict):
    code: str            # 待修复的代码
    error_message: str   # executor 捕获的报错
    analysis: str        # DeepSeek 的分析报告
    attempts: int        # 当前重试次数
    is_fixed: bool       # 是否修复成功的标志位

# 2. 模型加载工厂
def get_model(purpose: str):
    """
    全部切换为硅基流动的 DeepSeek 模型
    """
    # 硅基流动建议使用的模型 ID
    # 诊断建议用 R1 (推理强)，修复建议用 V3 (生成稳且快)
    model_name = "Pro/deepseek-ai/DeepSeek-R1" if purpose == "diagnose" else "deepseek-ai/DeepSeek-V4-Flash"
    
    return ChatOpenAI(
        model=model_name,
        openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
        openai_api_base=os.getenv("DEEPSEEK_API_BASE"),
        temperature=0.7 if purpose == "repair" else 0.3 # 诊断要严谨，修复可以稍微灵活
    )

# --- 3. 节点函数定义 ---

def diagnose_node(state: AgentState):
    print(f"🔎 [Node: Diagnose] 正在分析错误原因 (第 {state['attempts']+1} 次尝试)...")
    model = get_model("diagnose")
    prompt = f"源代码内容：\n{state['code']}\n\n报错信息：\n{state['error_message']}"
    
    response = model.invoke([
        ("system", DIAGNOSE_SYSTEM_PROMPT),
        ("user", prompt)
    ])
    return {"analysis": response.content}

def repair_node(state: AgentState):
    print("🛠️ [Node: Repair] 正在生成修复方案...")
    model = get_model("repair")
    prompt = f"原始代码：\n{state['code']}\n\n诊断报告：\n{state['analysis']}"
    
    response = model.invoke([
        ("system", REPAIR_SYSTEM_PROMPT),
        ("user", prompt)
    ])
    # 稍微清理一下 LLM 可能带的 Markdown 标签
    new_code = response.content.replace("```python", "").replace("```", "").strip()
    return {"code": new_code}

def verify_node(state: AgentState):
    print("🧪 [Node: Verify] 正在执行代码验证...")
    executor = CodeExecutor()
    result = executor.run_code(state["code"])
    
    if result["success"]:
        print("✅ 修复成功！代码已可以正常运行。")
        return {"is_fixed": True, "error_message": "", "attempts": state["attempts"] + 1}
    else:
        print(f"❌ 依然存在错误：{result['error'].splitlines()[-1]}")
        return {"is_fixed": False, "error_message": result["error"], "attempts": state["attempts"] + 1}

# 4. 跳转逻辑控制
def decide_to_continue(state: AgentState):
    if state["is_fixed"]:
        return "end"
    if state["attempts"] >= 3: # 最大重试 3 次
        print("⚠️ 已达到最大重试次数，修复终止。")
        return "end"
    return "continue"

# 5. 组装工作流图
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