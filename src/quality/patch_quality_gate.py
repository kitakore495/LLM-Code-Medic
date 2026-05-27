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
        # 必须存在 target_files
        # =====================================================
        if not target_files:

            return (
                False,
                "target_files 为空"
            )

        # =====================================================
        # Rule 2
        # 必须修改 target file
        # =====================================================
        modified_targets = []

        for file_path in target_files:

            old_code = (
                original_files.get(
                    file_path,
                    ""
                )
            )

            new_code = (
                repaired_files.get(
                    file_path,
                    ""
                )
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
        # Rule 3
        # Patch Empty
        # =====================================================
        for file_path in modified_targets:

            content = (
                repaired_files.get(
                    file_path,
                    ""
                )
            )

            if not content.strip():

                return (
                    False,
                    f"{file_path} "
                    "为空文件"
                )

        # =====================================================
        # Rule 4
        # 防止大规模无关修改
        # =====================================================
        modified_files = []

        for path in repaired_files:

            old = (
                original_files.get(
                    path,
                    ""
                )
            )

            new = (
                repaired_files.get(
                    path,
                    ""
                )
            )

            if old != new:

                modified_files.append(
                    path
                )

        unrelated = [

            x
            for x in modified_files
            if x not in target_files
        ]

        if len(unrelated) >= 3:

            return (
                False,
                "修改过多无关文件"
            )

        print(
            "✅ [PatchGate] "
            "质量检查通过"
        )

        return (
            True,
            "PASS"
        )