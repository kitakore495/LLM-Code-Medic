import os
import time
from dotenv import load_dotenv
from src.agent.graph import app
from src.tools.executor import CodeExecutor
from src.tools.scanner import ProjectScanner  # ✨ V2 引入全景扫描器

load_dotenv()

def run_medic(file_path, repo_root=None):
    """
    file_path: 发生报错的目标文件路径
    repo_root: 项目根目录。
               - 测 V1 单文件时传 None
               - 测 V2 仓库级 Bug 时传入对应的测试目录，如 "tests/v2_repo_case"
    """
    print(f"🚀 [Start] 准备修复文件: {file_path}")
    
    # 1. 检查并读取目标文件源码
    if not os.path.exists(file_path):
        print(f"❌ 错误：找不到文件 {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    # 2. 预运行一次，拿到初始报错环境
    print("🧪 正在进行初始运行以获取报错信息...")
    executor = CodeExecutor()
    # 初始预运行同样需要切入对应的仓库目录下，否则第一轮获取的报错可能不准
    initial_run = executor.run_code(code, repo_root=repo_root)
    
    if initial_run["success"]:
        print("✅ 代码本身没问题，不需要修复！")
        return

    # ✨ 3. V2 核心：如果指定了仓库根目录，进行全局扫描
    if repo_root and os.path.exists(repo_root):
        print(f"📂 检测到仓库模式，正在扫描全局项目结构: {repo_root} ...")
        scanner = ProjectScanner(root_path=repo_root)
        project_map = scanner.scan_structure()
        print("====== 项目目录结构地图 ======")
        print(project_map)
        print("==================================")
    else:
        project_map = f"单文件模式，无全局上下文。当前文件: {os.path.basename(file_path)}"

    # 4. 初始化 LangGraph 状态（注入 V2 的 project_map 与 repo_root 变量）
    initial_state = {
        "code": code,
        "error_message": initial_run["error"],
        "project_map": project_map,  # 给 AI 充当背景画布
        "repo_root": repo_root,      # 给验证节点切换运行目录
        "analysis": "",
        "attempts": 0,
        "is_fixed": False
    }

    # 5. 启动智能体流转
    final_state = app.invoke(initial_state, {"recursion_limit": 20})

    # 6. 结果产出与保存
    if final_state.get("is_fixed"):
        print("\n" + "="*30)
        print("🎉 修复完成！")
        print("="*30)

        if not os.path.exists("output"):
            os.makedirs("output")

        file_name = os.path.basename(file_path)
        output_path = os.path.join("output", f"fixed_{file_name}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_state["code"])

        print(f"✅ 修复后的代码已成功保存至: {output_path}")
        print("-" * 30)
        print(final_state["code"])
    else:
        print("\n❌ 修复失败，已达到重试上限。")

if __name__ == "__main__":
    # ====================================================
    # 💡 组长专用灰度测试开关：
    # ====================================================
    
    # 【测试场景 A】：复现和验证老版本的 V1 单文件修复能力
    # run_medic("tests/v1_single_file/debug_me.py", repo_root=None)
    
    # 【测试场景 B】：震撼跑通 V2 仓库级跨文件 Bug 修复能力
    run_medic("tests/v2_repo_case/main.py", repo_root="tests/v2_repo_case")