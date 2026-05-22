import os
import sys
from dotenv import load_dotenv

# =========================================================
# 全局环境变量必须最先加载
# =========================================================
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT_DIR, ".env")

load_dotenv(dotenv_path=ENV_PATH, override=True)

# 将项目根目录加入 PYTHONPATH
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.agent.graph import create_v3_medic_graph
from src.tools.scanner import ProjectScanner


def load_repo_files(repo_root: str):
    """
    装载测试仓库中的全部 Python 文件快照
    """
    repo_files = {}

    for root, _, files in os.walk(repo_root):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)

                # 统一为 repo_root 相对路径
                rel_path = os.path.relpath(full_path, repo_root)
                rel_path = rel_path.replace("\\", "/")

                with open(full_path, "r", encoding="utf-8") as f:
                    repo_files[rel_path] = f.read()

                print(f"   -> 已装载初始文件快照: {rel_path}")

    return repo_files


def main():
    print("==================================================")

    # =========================================================
    # 锁定测试战区
    # =========================================================
    TEST_REPO_ROOT = os.path.abspath("./tests/v3")

    print("🎬 启动 LLM-Code-Medic V3 多文件智能协同修复系统...")
    print(f"📂 当前目标测试仓库: {TEST_REPO_ROOT}")

    print("==================================================")

    if not os.path.exists(TEST_REPO_ROOT):
        print(f"❌ 错误: 未找到测试仓库路径 {TEST_REPO_ROOT}")
        return

    # =========================================================
    # Step 1 AST扫描
    # =========================================================
    print("\n[Step 1] 正在启动 AST 静态扫描器绘制全景地图...")

    scanner = ProjectScanner(repo_root=TEST_REPO_ROOT)
    project_map_context = scanner.scan()

    print("✅ 全景地图绘制完毕。")

    # =========================================================
    # Step 2 装载测试仓库
    # =========================================================
    print("\n[Step 2] 正在装载测试仓库源码快照...")

    initial_repo_files = load_repo_files(TEST_REPO_ROOT)

    # =========================================================
    # Step 3 初始报错
    # =========================================================
    INITIAL_ERROR = """
Traceback (most recent call last):
  File "main.py", line 11, in run_pipeline
    result = utils.compute_core_logic(input_data)
AttributeError: module 'utils' has no attribute 'compute_core_logic'
"""

    # =========================================================
    # Step 4 初始状态
    # =========================================================
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

    # =========================================================
    # Step 5 编译 LangGraph
    # =========================================================
    print("\n[Step 3] 正在编译 LangGraph 多文件状态机...")

    app = create_v3_medic_graph()

    # =========================================================
    # Step 6 启动
    # =========================================================
    print("\n[Step 4] 🚀 开始执行自动化修复流程...")

    final_state = app.invoke(initial_state)

    print("\n==================================================")

    if final_state.get("is_fixed"):
        print("🎉 修复成功")
    else:
        print("🚨 修复失败")

    print("==================================================")


if __name__ == "__main__":
    main()