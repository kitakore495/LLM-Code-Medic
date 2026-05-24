import re

from typing import Dict

from src.plugins.base_plugin import (
    BasePlugin
)


class UnitTestPlugin(
    BasePlugin
):

    name = "unit_test"

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
            "🧪 [Plugin] "
            "Unit Test Plugin 正在执行..."
        )

        python_files = []

        test_files = []

        for path in (
            repo_files.keys()
        ):

            if not path.endswith(
                ".py"
            ):
                continue

            if re.search(
                r"(^|/)test_.*\.py$",
                path
            ):

                test_files.append(
                    path
                )

            else:

                python_files.append(
                    path
                )

        print(
            f"📦 Python 文件数: "
            f"{len(python_files)}"
        )

        print(
            f"🧪 测试文件数: "
            f"{len(test_files)}"
        )

        missing_tests = []

        for file_path in (
            python_files
        ):

            base_name = (
                file_path
                .split("/")[-1]
                .replace(
                    ".py",
                    ""
                )
            )

            expected_test = (
                f"test_{base_name}.py"
            )

            exists = any(
                expected_test
                in test_file
                for test_file in (
                    test_files
                )
            )

            if not exists:

                missing_tests.append(
                    expected_test
                )

        if missing_tests:

            print(
                "\n⚠️ [UnitTest] "
                "发现缺失测试:"
            )

            for test in (
                missing_tests
            ):

                print(
                    f"   - 建议新增: "
                    f"{test}"
                )

        else:

            print(
                "✅ [UnitTest] "
                "测试覆盖结构正常"
            )

        print(
            "✅ [Plugin] "
            "Unit Test Plugin 执行完成"
        )

        return repo_files