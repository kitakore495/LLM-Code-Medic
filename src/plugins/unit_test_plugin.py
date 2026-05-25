import re

from typing import Dict

from src.plugins.base_plugin import (
    BasePlugin
)

from src.plugins.llm_test_generator import (
    LLMTestGenerator
)


class UnitTestPlugin(
    BasePlugin
):

    name = "unit_test"

    def __init__(
        self
    ):

        self.generator = (
            LLMTestGenerator()
        )

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
            "🧪 [Plugin] "
            "Unit Test Plugin 正在执行..."
        )

        python_files = []

        test_files = []

        # =====================================================
        # 分类源码 / 测试文件
        # =====================================================
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

        generated_count = 0

        # =====================================================
        # 检测缺失测试
        # =====================================================
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

            if exists:

                continue

            print(
                f"\n⚠️ [UnitTest] "
                f"发现缺失测试: "
                f"{expected_test}"
            )

            source_code = (
                repo_files[
                    file_path
                ]
            )

            generated_test = (
                self.generator
                .generate_test(
                    file_name=file_path,
                    code=source_code
                )
            )

            if not generated_test:

                print(
                    f"❌ [UnitTest] "
                    f"生成失败: "
                    f"{expected_test}"
                )

                continue

            # =================================================
            # 写入 repo_files
            # =================================================
            repo_files[
                expected_test
            ] = generated_test

            test_files.append(
                expected_test
            )

            generated_count += 1

            print(
                f"✅ [UnitTest] "
                f"已生成: "
                f"{expected_test}"
            )

        # =====================================================
        # Summary
        # =====================================================
        print(
            "\n📊 [UnitTest] "
            f"本次生成测试文件数: "
            f"{generated_count}"
        )

        print(
            "✅ [Plugin] "
            "Unit Test Plugin 执行完成"
        )

        return repo_files