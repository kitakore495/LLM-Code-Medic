import os
from dotenv import load_dotenv
from src.agent.graph import app
from src.tools.executor import CodeExecutor

load_dotenv()

def run_medic(file_path):
    print(f"🚀 [Start] 准备修复文件: {file_path}")
    
    # 1. 读取原始代码
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    # 2. 预运行一次，拿到初始报错（这样智能体一进来就有目标）
    print("🧪 正在进行初始运行以获取报错信息...")
    executor = CodeExecutor()
    initial_run = executor.run_code(code)
    
    if initial_run["success"]:
        print("✅ 代码本身没问题，不需要修复！")
        return

    # 3. 初始化 LangGraph 状态
    initial_state = {
        "code": code,
        "error_message": initial_run["error"],
        "analysis": "",
        "attempts": 0,
        "is_fixed": False
    }

    # 4. 运行智能体工作流
    # config 可以设置递归深度，防止死循环
    final_state = app.invoke(initial_state, {"recursion_limit": 20})

    # 5. 输出结果
    if final_state.get("is_fixed"):
        print("\n" + "="*30)
        print("🎉 修复完成！")
        print("="*30)
        print(final_state["code"])
    else:
        print("\n❌ 修复失败，已达到尝试上限。")

if __name__ == "__main__":
    # 确保路径指向你刚创建的文件
    run_medic("debug_me.py")