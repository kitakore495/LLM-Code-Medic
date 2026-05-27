import re

from typing import Dict
from typing import List
class SemanticPatchGate:

    # =========================================================
    # Check
    # =========================================================
    def check(
        self,
        repo_files: Dict[str, str],
        original_repo_files: Dict[str, str],
        analysis: str,
        target_files=None
    ):

        print(
            "\n🧠 [SemanticGate] "
            "开始执行语义补丁检查..."
        )

        reasons = []

        if target_files is None:

            target_files = []

        # =====================================================
        # Rule 1
        # target_files 必须真正发生修改
        # =====================================================
        changed_files = set()

        for path in target_files:

            old_code = (
                original_repo_files.get(
                    path,
                    ""
                )
            )

            new_code = (
                repo_files.get(
                    path,
                    ""
                )
            )

            if old_code != new_code:

                changed_files.add(
                    path.lower()
                )

        for file_name in target_files:

            if (
                file_name.lower()
                not in changed_files
            ):

                reasons.append(
                    f"{file_name} "
                    "被要求修复但未修改"
                )

        # =====================================================
        # Rule 2
        # 可疑 workaround patch
        # =====================================================
        suspicious_patterns = [

            # magic workaround
            r"adjusted_weight\s*=\s*1\b",

            r"if\s+.*==\s*0\s*:",

            r"if\s+.*<=\s*0\s*:",

            r"max\s*\(",

            r"min\s*\(",

            # 提前 return 绕过公式
            r"if\s+.*==.*:\s*return",

            r"if\s+.*<=.*:\s*return",

            r"if\s+.*>=.*:\s*return",

            r"if\s+.*:\s*return\s+[A-Za-z0-9_\.\*\+\-/\(\)\s]+"
        ]

        files_to_check = (
            target_files
            if target_files
            else repo_files.keys()
        )

        for path in files_to_check:

            old_code = (
                original_repo_files.get(
                    path,
                    ""
                )
            )

            new_code = (
                repo_files.get(
                    path,
                    ""
                )
            )

            # 没改不查
            if old_code == new_code:

                continue

            for pattern in (
                suspicious_patterns
            ):

                if re.search(
                    pattern,
                    new_code,
                    re.DOTALL
                ):

                    reasons.append(
                        f"{path} "
                        "疑似 workaround patch"
                    )

                    break

        # =====================================================
        # Rule 3
        # Empty Logic
        # =====================================================
        suspicious_logic = [

            "pass",

            "return None",

            "return True",

            "return 1"
        ]

        for path in files_to_check:

            code = (
                repo_files.get(
                    path,
                    ""
                )
            )

            for item in (
                suspicious_logic
            ):

                if item in code:

                    reasons.append(
                        f"{path} "
                        "疑似逻辑绕过"
                    )

                    break

        # =====================================================
        # Rule 4
        # except: pass
        # =====================================================
        for path in files_to_check:

            code = (
                repo_files.get(
                    path,
                    ""
                )
            )

            if re.search(

                r"except\s*:\s*pass",
                code
            ):

                reasons.append(
                    f"{path} "
                    "检测到 except pass"
                )

        # =====================================================
        # Result
        # =====================================================
        if reasons:

            reason = (
                "；".join(
                    reasons
                )
            )

            print(
                "❌ [SemanticGate] "
                "检查失败"
            )

            print(
                f"原因: {reason}"
            )

            return (
                False,
                reason
            )

        print(
            "✅ [SemanticGate] "
            "检查通过"
        )

        return (
            True,
            "OK"
        )