import re
from typing import Dict, List


class PatchQualityGate:

    def check(
        self,
        analysis: str,
        original_files: Dict[str, str],
        repaired_files: Dict[str, str],
        target_files: List[str],
        last_patch_files: List[str] = None,
        bug_inventory: str = "",
    ) -> tuple[bool, str]:

        print("\n🛡️ [PatchGate] 开始执行补丁质量检查...")

        # ==================================================
        # Rule 1
        # ==================================================

        if not target_files:
            return False, "target_files 为空"

        # ==================================================
        # Rule 2
        # ==================================================

        modified_targets = [
            f
            for f in target_files
            if original_files.get(f, "")
            != repaired_files.get(f, "")
        ]

        if not modified_targets:
            return False, "未修改目标文件"

        # ==================================================
        # Rule 3
        # ==================================================

        for file_path in modified_targets:

            if not repaired_files.get(
                file_path,
                ""
            ).strip():

                return (
                    False,
                    f"{file_path} 为空文件"
                )

        # ==================================================
        # Rule 4
        # ==================================================

        if last_patch_files is not None:

            unrelated = [
                f
                for f in last_patch_files
                if f not in target_files
            ]

        else:

            all_modified = [
                f
                for f in repaired_files
                if original_files.get(f, "")
                != repaired_files.get(f, "")
            ]

            unrelated = [
                f
                for f in all_modified
                if f not in target_files
            ]

        if len(unrelated) > 20:

            return (
                False,
                f"本轮 patch 修改了过多无关文件（{len(unrelated)} 个）: {unrelated}"
            )

        # ==================================================
        # Rule 5
        #
        # BUG_INVENTORY 涉及的目标文件
        # 至少要有一个出现在本轮 Patch 中
        #
        # 防止：
        # Diagnose 说问题在 order_service.py
        # LLM 却只改 notification_service.py
        # ==================================================

        if (
            bug_inventory
            and last_patch_files
        ):

            inventory_files = set()

            for f in re.findall(
                r'([A-Za-z0-9_\-/]+\.py)',
                bug_inventory
            ):

                inventory_files.add(
                    f.replace(
                        "\\",
                        "/"
                    )
                )

            target_inventory_files = {

                f

                for f in inventory_files

                if f in target_files

            }

            if target_inventory_files:

                touched = any(
                    f in last_patch_files
                    for f in target_inventory_files
                )

                if not touched:

                    return (
                        False,
                        "BUG_INVENTORY 涉及文件未出现在本轮 Patch 中: "
                        f"{sorted(target_inventory_files)}"
                    )

        print("✅ [PatchGate] 质量检查通过")

        return True, "PASS"