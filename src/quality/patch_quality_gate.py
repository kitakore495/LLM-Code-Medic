from typing import Dict, List


class PatchQualityGate:

    def check(
        self,
        analysis: str,
        original_files: Dict[str, str],
        repaired_files: Dict[str, str],
        target_files: List[str],
        last_patch_files: List[str] = None,  # 本轮 LLM 实际输出的文件
    ) -> tuple[bool, str]:

        print("\n🛡️ [PatchGate] 开始执行补丁质量检查...")

        # Rule 1: target_files 不能为空
        if not target_files:
            return False, "target_files 为空"

        # Rule 2: target_files 中至少有一个文件被实际修改
        modified_targets = [
            f for f in target_files
            if original_files.get(f, "") != repaired_files.get(f, "")
        ]
        if not modified_targets:
            return False, "未修改目标文件"

        # Rule 3: 修改后的目标文件不能为空
        for file_path in modified_targets:
            if not repaired_files.get(file_path, "").strip():
                return False, f"{file_path} 为空文件"

        # Rule 4: 本轮 patch 不能修改过多无关文件
        # 优先用 last_patch_files（本轮 LLM 实际输出的文件列表），
        # 避免用 original_files 做全量 diff 时把历史累积修改也算进去
        if last_patch_files is not None:
            unrelated = [f for f in last_patch_files if f not in target_files]
        else:
            # 兜底：和初始快照做全量 diff（旧行为，仅在 last_patch_files 未传时使用）
            all_modified = [
                f for f in repaired_files
                if original_files.get(f, "") != repaired_files.get(f, "")
            ]
            unrelated = [f for f in all_modified if f not in target_files]

        if len(unrelated) > 20:
            return False, f"本轮 patch 修改了过多无关文件（{len(unrelated)} 个）: {unrelated}"

        print("✅ [PatchGate] 质量检查通过")
        return True, "PASS"