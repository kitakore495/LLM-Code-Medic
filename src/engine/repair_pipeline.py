import os

from src.agent.graph import (
    create_v3_medic_graph
)

from src.tools.scanner import (
    ProjectScanner
)


class RepairPipeline:

    def __init__(self):

        self.test_repo_root = os.path.abspath(
            "./tests/v3"
        )

    # =========================================================
    # 装载仓库文件快照
    # =========================================================
    def load_repo_files(self):

        repo_files = {}

        for root, _, files in os.walk(
            self.test_repo_root
        ):

            for file in files:

                if file.endswith(".py"):

                    full_path = os.path.join(
                        root,
                        file
                    )

                    rel_path = os.path.relpath(
                        full_path,
                        self.test_repo_root
                    )

                    rel_path = rel_path.replace(
                        "\\",
                        "/"
                    )

                    with open(
                        full_path,
                        "r",
                        encoding="utf-8"
                    ) as f:

                        repo_files[
                            rel_path
                        ] = f.read()

                    print(
                        f"   -> 已装载初始文件快照: "
                        f"{rel_path}"
                    )

        return repo_files

    # =========================================================
    # 执行主流程
    # =========================================================
    def execute(self):

        print(
            "=================================================="
        )

        print(
            "🎬 启动 LLM-Code-Medic V4 多文件智能协同修复系统..."
        )

        print(
            f"📂 当前目标测试仓库: "
            f"{self.test_repo_root}"
        )

        print(
            "=================================================="
        )

        if not os.path.exists(
            self.test_repo_root
        ):

            print(
                f"❌ 错误: "
                f"未找到测试仓库路径 "
                f"{self.test_repo_root}"
            )

            return

        # =====================================================
        # Step 1 AST 扫描
        # =====================================================
        print(
            "\n[Step 1] "
            "正在启动 AST 静态扫描器绘制全景地图..."
        )

        scanner = ProjectScanner(
            repo_root=self.test_repo_root
        )

        project_map_context = (
            scanner.scan()
        )

        print("✅ 全景地图绘制完毕。")

        # =====================================================
        # Step 2 装载源码
        # =====================================================
        print(
            "\n[Step 2] "
            "正在装载测试仓库源码快照..."
        )

        initial_repo_files = (
            self.load_repo_files()
        )

        # =====================================================
        # Step 3 初始报错
        # =====================================================
        initial_error = """
Traceback (most recent call last):
  File "main.py", line 11, in run_pipeline
    result = utils.compute_core_logic(input_data)
AttributeError: module 'utils' has no attribute 'compute_core_logic'
"""

        # =====================================================
        # Step 4 初始状态
        # =====================================================
        initial_state = {
            "repo_root":
                self.test_repo_root,

            "project_map":
                project_map_context,

            "error_message":
                initial_error.strip(),

            "target_files":
                [],

            "repo_files":
                initial_repo_files,

            "attempts":
                0,

            "is_fixed":
                False,

            "analysis":
                ""
        }

        # =====================================================
        # Step 5 编译 Graph
        # =====================================================
        print(
            "\n[Step 3] "
            "正在编译 LangGraph 多文件状态机..."
        )

        app = create_v3_medic_graph()

        # =====================================================
        # Step 6 执行
        # =====================================================
        print(
            "\n[Step 4] "
            "🚀 开始执行自动化修复流程..."
        )

        final_state = app.invoke(
            initial_state
        )

        print(
            "\n=================================================="
        )

        if final_state.get(
            "is_fixed"
        ):

            print("🎉 修复成功")

        else:

            print("🚨 修复失败")

        print(
            "=================================================="
        )