from typing import Dict
from typing import List

from src.plugins.base_plugin import (
    BasePlugin
)

from src.plugins.style_plugin import (
    StylePlugin
)

from src.plugins.security_plugin import (
    SecurityPlugin
)

from src.plugins.unit_test_plugin import (
    UnitTestPlugin
)


class PluginManager:

    def __init__(
        self
    ):

        self.plugins: List[
            BasePlugin
        ] = []

        self._register_default_plugins()

    # =====================================================
    # 注册默认插件
    # =====================================================
    def _register_default_plugins(
        self
    ):

        self.register_plugin(
            StylePlugin()
        )

        self.register_plugin(
            SecurityPlugin()
        )

        self.register_plugin(
            UnitTestPlugin()
        )

    # =====================================================
    # 注册插件
    # =====================================================
    def register_plugin(
        self,
        plugin: BasePlugin
    ):

        print(
            f"🔌 [Plugin] 注册插件: "
            f"{plugin.name}"
        )

        self.plugins.append(
            plugin
        )

    # =====================================================
    # 执行所有插件
    # =====================================================
    def run_all(
        self,
        repo_files: Dict[
            str,
            str
        ],
        analysis: str
    ) -> Dict[
        str,
        str
    ]:

        if not self.plugins:

            print(
                "⚠️ [Plugin] "
                "无可执行插件"
            )

            return repo_files

        updated_repo_files = (
            repo_files
        )

        print(
            "\n🧩 [Plugin] "
            "开始执行插件流水线..."
        )

        for plugin in (
            self.plugins
        ):

            try:

                print(
                    f"\n🚀 [Plugin] "
                    f"执行: "
                    f"{plugin.name}"
                )

                updated_repo_files = (
                    plugin.run(
                        repo_files=(
                            updated_repo_files
                        ),
                        analysis=analysis
                    )
                )

            except Exception as e:

                print(
                    f"❌ [Plugin] "
                    f"{plugin.name} "
                    f"执行失败: {e}"
                )

        print(
            "\n✅ [Plugin] "
            "插件流水线执行完成"
        )

        return (
            updated_repo_files
        )