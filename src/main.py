import os
import time
from dotenv import load_dotenv
from src.agent.graph import app
from src.tools.executor import CodeExecutor

load_dotenv()

def run_medic(file_path):
    print(f"🚀 [Start] 准备修复文件: {file_path}")
    
    # 1. 读取原始代码
    if not os.path.exists(file_path):
        print(f"❌ 错误：找不到文件 {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    # 2. 预运行一次，拿到初始报错
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
    # 注意：这里的 app 是从 src.agent.graph 导入的
    final_state = app.invoke(initial_state, {"recursion_limit": 20})

    # 5. 输出结果并保存到 output 文件夹 (V1 完结版改进)
    if final_state.get("is_fixed"):
        print("\n" + "="*30)
        print("🎉 修复完成！")
        print("="*30)

        # 确保 output 目录存在
        if not os.path.exists("output"):
            os.makedirs("output")

        # 生成输出路径，例如 output/fixed_debug_me.py
        file_name = os.path.basename(file_path)
        output_path = os.path.join("output", f"fixed_{file_name}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_state["code"])

        print(f"✅ 修复后的代码已保存至: {output_path}")
        print("-" * 30)
        print(final_state["code"])
    else:
        print("\n❌ 修复失败，已达到尝试上限。")

if __name__ == "__main__":
    # 修改路径指向 tests 目录
    run_medic("tests/debug_me.py")