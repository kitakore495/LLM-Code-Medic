import re

from typing import Dict
from typing import List


class PatchQualityGate:

    # =========================================================
    # Entry
    # =========================================================
    def check(
        self,
        analysis: str,
        original_files: Dict[str, str],
        repaired_files: Dict[str, str],
        target_files: List[str]
    ) -> tuple[bool, str]:

        print(
            "\n🛡️ [PatchGate] "
            "开始执行补丁质量检查..."
        )

        # =====================================================
        # Rule 1
        # 必须修改目标文件
        # =====================================================
        modified_targets = []

        for file_path in target_files:

            old_code = original_files.get(
                file_path,
                ""
            )

            new_code = repaired_files.get(
                file_path,
                ""
            )

            if old_code != new_code:

                modified_targets.append(
                    file_path
                )

        if not modified_targets:

            return (
                False,
                "未修改目标文件"
            )

        # =====================================================
        # Rule 2
        # Magic Number Workaround
        # =====================================================
        suspicious = (
            self._detect_magic_number_patch(
                original_files,
                repaired_files
            )
        )

        if suspicious:

            return (
                False,
                "疑似 workaround patch "
                "(magic number modification)"
            )

        # =====================================================
        # Rule 3
        # Hack patch
        # =====================================================
        hacked = (
            self._detect_hack_patch(
                repaired_files
            )
        )

        if hacked:

            return (
                False,
                "疑似 hack patch"
            )

        print(
            "✅ [PatchGate] "
            "质量检查通过"
        )

        return (
            True,
            "PASS"
        )

    # =========================================================
    # Detect Magic Number Change
    # =========================================================
    def _detect_magic_number_patch(
        self,
        original_files: Dict[str, str],
        repaired_files: Dict[str, str]
    ) -> bool:

        pattern = re.compile(
            r"\b\d+\b"
        )

        for path in repaired_files:

            old = (
                original_files.get(
                    path,
                    ""
                )
            )

            new = repaired_files[
                path
            ]

            old_numbers = (
                pattern.findall(
                    old
                )
            )

            new_numbers = (
                pattern.findall(
                    new
                )
            )

            if (
                old_numbers != new_numbers
                and
                len(old_numbers)
                == len(new_numbers)
            ):

                diff_count = sum(
                    1
                    for a, b in zip(
                        old_numbers,
                        new_numbers
                    )
                    if a != b
                )

                # 只改了少数数字
                if diff_count <= 2:

                    print(
                        "⚠️ [PatchGate] "
                        "检测到可疑 magic number 修改"
                    )

                    return True

        return False

    # =========================================================
    # Detect Hack Patch
    # =========================================================
    def _detect_hack_patch(
        self,
        repaired_files: Dict[str, str]
    ) -> bool:

        suspicious_patterns = [

            r"except\s*:\s*pass",

            r"return\s+1\b",

            r"return\s+True\b",

            r"return\s+None\b"
        ]

        for content in (
            repaired_files.values()
        ):

            for pattern in (
                suspicious_patterns
            ):

                if re.search(
                    pattern,
                    content
                ):

                    print(
                        "⚠️ [PatchGate] "
                        "检测到 hack patch"
                    )

                    return True

        return False