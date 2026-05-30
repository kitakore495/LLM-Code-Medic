from src.agent.graph import (
    create_v4_medic_graph
)

from src.tools.scanner import (
    ProjectScanner
)

from src.config.runtime_config import (
    runtime_config
)

from src.plugins.plugin_manager import (
    PluginManager
)


class RepairPipeline:

    def __init__(
        self,
        repo_root: str
    ):

        self.repo_root = (
            repo_root
        )

        # =====================================================
        # Plugin Manager
        # =====================================================
        self.plugin_manager = (
            PluginManager()
        )

    # =========================================================
    # 装载仓库源码快照
    # =========================================================
    def load_repo_files(
        self
    ):

        import os

        repo_files = {}

        for (
            root,
            _,
            files
        ) in os.walk(
            self.repo_root
        ):

            for file in files:

                if not file.endswith(
                    ".py"
                ):
                    continue

                full_path = (
                    os.path.join(
                        root,
                        file
                    )
                )

                rel_path = (
                    os.path.relpath(
                        full_path,
                        self.repo_root
                    )
                )

                rel_path = (
                    rel_path.replace(
                        "\\",
                        "/"
                    )
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
                    "   -> 已装载初始文件快照: "
                    f"{rel_path}"
                )

        return repo_files

    # =========================================================
    # 主执行流程
    # =========================================================
    def execute(
        self
    ):

        print(
            "\n[Step 1] "
            "正在启动 AST "
            "静态扫描器绘制全景地图..."
        )

        scanner = (
            ProjectScanner(
                repo_root=(
                    self.repo_root
                )
            )
        )

        project_map_context = (
            scanner.scan()
        )

        print(
            "✅ 全景地图绘制完毕。"
        )

        print(
            "\n[Step 2] "
            "正在装载测试仓库源码快照..."
        )

        initial_repo_files = (
            self.load_repo_files()
        )

        # =====================================================
        # 初始错误
        # =====================================================
        INITIAL_ERROR = """
Traceback (most recent call last):
  File "main.py", line 11, in run_pipeline
    result = utils.compute_core_logic(input_data)
AttributeError: module 'utils' has no attribute 'compute_core_logic'
""".strip()

        print(
            "\n🧠 当前运行配置"
        )

        print(
            f"   Diagnose: "
            f"{runtime_config.diagnose_provider}"
            f" | "
            f"{runtime_config.diagnose_model}"
        )

        print(
            f"   Repair: "
            f"{runtime_config.repair_provider}"
            f" | "
            f"{runtime_config.repair_model}"
        )

        # =====================================================
        # 初始状态
        # =====================================================
        initial_state = {

            "repo_root":
                self.repo_root,

            "project_map":
                project_map_context,

            "error_message":
                INITIAL_ERROR,

            "target_files":
                [],

            # 当前仓库
            "repo_files":
                initial_repo_files.copy(),

            # 原始快照（Gate比较用）
            "original_repo_files":
                initial_repo_files.copy(),

            "repair_attempts":
                0,

            "is_fixed":
                False,

            "analysis":
                "",

            # sandbox
            "sandbox_stdout":
                "",

            "sandbox_stderr":
                "",

            # patch gate
            "patch_quality_passed":
                False,

            "patch_quality_reason":
                "",

            # semantic gate
            "semantic_gate_passed":
                False,

            "semantic_gate_reason":
                ""
        }

        print(
            "\n[Step 3] "
            "正在编译 LangGraph "
            "多文件状态机..."
        )

        app = (
            create_v4_medic_graph()
        )

        print(
            "\n[Step 4] 🚀 "
            "开始执行自动化修复流程..."
        )

        final_state = (
            app.invoke(
                initial_state
            )
        )

        # =====================================================
        # Plugin Pipeline
        # =====================================================
        print(
            "\n[Step 5] 🧩 "
            "执行 Plugin System..."
        )

        updated_repo_files = (
            self.plugin_manager
            .run_all(
                repo_files=(
                    final_state[
                        "repo_files"
                    ]
                ),
                analysis=(
                    final_state[
                        "analysis"
                    ]
                )
            )
        )

        final_state[
            "repo_files"
        ] = updated_repo_files

        print(
            "\n"
            "=================================================="
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