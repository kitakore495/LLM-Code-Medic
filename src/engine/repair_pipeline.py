import os

from src.agent.graph import (
    create_v4_medic_graph
)

from src.tools.scanner import (
    ProjectScanner
)


class RepairPipeline:

    def __init__(self):

        # =====================================================
        # 锁定测试战区
        # =====================================================
        self.repo_root = os.path.abspath(
            "./tests/v3"
        )

    # =========================================================
    # 装载测试仓库源码
    # =========================================================
    def _load_repo_files(self):

        repo_files = {}

        print(
            "\n[Step 2] 正在装载测试仓库源码快照..."
        )

        for root, _, files in os.walk(
            self.repo_root
        ):

            for file in files:

                if file.endswith(".py"):

                    full_path = os.path.join(
                        root,
                        file
                    )

                    rel_path = os.path.relpath(
                        full_path,
                        self.repo_root
                    )

                    rel_path = (
                        rel_path
                        .replace("\\", "/")
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
    # 初始报错（后续改成真实运行捕获）
    # =========================================================
    def _build_initial_error(self):

        return """
Traceback (most recent call last):
  File "main.py", line 11, in run_pipeline
    result = utils.compute_core_logic(input_data)
AttributeError: module 'utils' has no attribute 'compute_core_logic'
""".strip()

    # =========================================================
    # 执行修复流程
    # =========================================================
    def execute(self):

        # =====================================================
        # Step 1 AST 扫描
        # =====================================================
        print(
            "\n[Step 1] 正在启动 AST 静态扫描器绘制全景地图..."
        )

        scanner = ProjectScanner(
            repo_root=self.repo_root
        )

        project_map_context = (
            scanner.scan()
        )

        print(
            "✅ 全景地图绘制完毕。"
        )

        # =====================================================
        # Step 2 装载仓库源码
        # =====================================================
        initial_repo_files = (
            self._load_repo_files()
        )

        # =====================================================
        # Step 3 初始状态
        # =====================================================
        initial_state = {
            "repo_root":
                self.repo_root,

            "project_map":
                project_map_context,

            "error_message":
                self._build_initial_error(),

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
        # Step 4 编译 Graph
        # =====================================================
        print(
            "\n[Step 3] 正在编译 LangGraph 多文件状态机..."
        )

        app = (
            create_v4_medic_graph()
        )

        # =====================================================
        # Step 5 启动自动修复
        # =====================================================
        print(
            "\n[Step 4] 🚀 开始执行自动化修复流程..."
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

            print(
                "🎉 修复成功"
            )

        else:

            print(
                "🚨 修复失败"
            )

        print(
            "=================================================="
        )