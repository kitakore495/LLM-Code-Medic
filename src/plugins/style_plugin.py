from typing import Dict

from src.plugins.base_plugin import (
    BasePlugin
)


class StylePlugin(
    BasePlugin
):

    name = "style"

    def run(
        self,
        repo_files: Dict[str, str],
        analysis: str
    ) -> Dict[str, str]:

        print(
            "🎨 [Plugin] "
            "Style Plugin 正在执行..."
        )

        updated_files = {}

        for (
            file_path,
            content
        ) in repo_files.items():

            if not isinstance(
                content,
                str
            ):
                updated_files[
                    file_path
                ] = content
                continue

            cleaned = (
                self
                ._normalize_code(
                    content
                )
            )

            updated_files[
                file_path
            ] = cleaned

        print(
            "✅ [Plugin] "
            "Style Plugin 执行完成"
        )

        return updated_files

    # =====================================================
    # Style Normalize
    # =====================================================
    def _normalize_code(
        self,
        content: str
    ) -> str:

        lines = []

        for line in (
            content.splitlines()
        ):

            # 去尾空格
            cleaned_line = (
                line.rstrip()
            )

            lines.append(
                cleaned_line
            )

        normalized = (
            "\n".join(lines)
        )

        # 文件结尾统一换行
        normalized = (
            normalized.rstrip()
            + "\n"
        )

        return normalized