import re

from typing import Dict

from src.plugins.base_plugin import (
    BasePlugin
)


class SecurityPlugin(
    BasePlugin
):

    name = "security"

    def __init__(
        self
    ):

        self.rules = {

            "eval(":
                r"\beval\s*\(",

            "exec(":
                r"\bexec\s*\(",

            "os.system(":
                r"os\.system\s*\(",

            "subprocess shell=True":
                r"shell\s*=\s*True",

            "pickle.loads(":
                r"pickle\.loads\s*\("
        }

    # =====================================================
    # Plugin Run
    # =====================================================
    def run(
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

        print(
            "🔒 [Plugin] "
            "Security Plugin 正在执行..."
        )

        findings = []

        for (
            file_path,
            content
        ) in repo_files.items():

            if not isinstance(
                content,
                str
            ):
                continue

            file_findings = (
                self._scan_file(
                    file_path,
                    content
                )
            )

            findings.extend(
                file_findings
            )

        if findings:

            print(
                "\n🚨 [Security] "
                "发现潜在安全风险:"
            )

            for item in findings:

                print(
                    f"   - {item}"
                )

        else:

            print(
                "✅ [Security] "
                "未发现明显高危模式"
            )

        print(
            "✅ [Plugin] "
            "Security Plugin 执行完成"
        )

        return repo_files

    # =====================================================
    # Scan File
    # =====================================================
    def _scan_file(
        self,
        file_path: str,
        content: str
    ):

        findings = []

        lines = (
            content.splitlines()
        )

        for (
            line_no,
            line
        ) in enumerate(
            lines,
            start=1
        ):

            for (
                rule_name,
                pattern
            ) in (
                self.rules.items()
            ):

                if re.search(
                    pattern,
                    line
                ):

                    findings.append(
                        f"{file_path}"
                        f":{line_no}"
                        f" -> "
                        f"{rule_name}"
                    )

        return findings