import os
import sys
from dotenv import load_dotenv  # 👈 【核心修复】引入全局环境加载器

# 👈 【核心修复】必须在程序刚刚启动的第一秒，强行把全局 .env 文件读取进内存
load_dotenv()

# 将项目根目录加入环境变量，防止组件导入迷路
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.graph import create_v3_medic_graph
from src.tools.scanner import ProjectScanner

def main():
    print("==================================================")
    # 🎯 ✅ 组长请锁定：路径已物理对齐到全新的 tests/v3 战区
    TEST_REPO_ROOT = os.path.abspath("./tests/v3") 
    print(f"🎬 启动 LLM-Code-Medic V3 多文件智能协同修复系统...")
    print(f"📂 当前目标测试仓库: {TEST_REPO_ROOT}")
    print("==================================================")

    if not os.path.exists(TEST_REPO_ROOT):
        print(f"❌ 错误: 未找到测试仓库路径 {TEST_REPO_ROOT}，请检查目录结构！")
        return

    # 1. 启动静态雷达：调用 Scanner 自动绘制项目全景 AST 地图
    print("\n[Step 1] 正在启动 AST 静态扫描器绘制全景地图...")
    scanner = ProjectScanner(repo_root=TEST_REPO_ROOT)
    project_map_context = scanner.scan() 
    print("✅ 全景地图绘制完毕。")

    # 2. 灵魂装配: 扫描并读取测试仓库里所有 Python 文件的初始全量代码
    print("\n[Step 2] 正在将测试仓库所有初始源码装载进 V3 状态机内存...")
    initial_repo_files = {}
    
    for root, _, files in os.walk(TEST_REPO_ROOT):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                # 计算出相对路径，例如 "main.py" 或 "utils.py"
                rel_path = os.path.relpath(full_path, TEST_REPO_ROOT)
                
                with open(full_path, "r", encoding="utf-8") as f:
                    initial_repo_files[rel_path] = f.read()
                    print(f"   -> 已装载初始文件快照: {rel_path}")

    # 3. 构造第一次运行的初始报错信息，作为引子喂给 R1
    INITIAL_ERROR = """
Traceback (most recent call last):
  File "main.py", line 11, in run_pipeline
    result = utils.compute_core_logic(input_data)
AttributeError: module 'utils' has no attribute 'compute_core_logic'
"""

    # 4. 初始化 V3 状态机参数
    initial_state = {
        "repo_root": TEST_REPO_ROOT,
        "project_map": project_map_context,
        "error_message": INITIAL_ERROR.strip(),
        "target_files": [],
        "repo_files": initial_repo_files,
        "attempts": 0,
        "is_fixed": False,
        "analysis": ""
    }

    # 5. 构建并编译 LangGraph 拓扑网
    print("\n[Step 3] 正在编译 LangGraph 多文件有向图工作流...")
    v3_app = create_v3_medic_graph()

    # 6. 一脚油门，流转通电！
    print("\n[Step 4] 🚀 智能体正式具身合流，开始全自动多文件联合审计与测试...")
    final_state = v3_app.invoke(initial_state)

    print("\n==================================================")
    if final_state.get("is_fixed"):
        print("🎉【大获全胜】V3 智能体成功在 3 轮内完成了多文件协同修复！")
        print("💡 修复后的全量代码已安全驻留在磁盘测试目录中。")
    else:
        print("🚨【遗憾收工】未能完成修复，请检查大模型提示词约束或测试仓库复杂度。")
    print("==================================================")

if __name__ == "__main__":
    main()