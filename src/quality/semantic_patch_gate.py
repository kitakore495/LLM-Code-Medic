import re

from typing import Dict


class SemanticPatchGate:

    # =========================================================
    # Evaluate
    # =========================================================
    @staticmethod
    def evaluate(
        repo_files: Dict[
            str,
            str
        ],
        analysis: str,
        patch: str = ""
    ):

        print(
            "\n🧠 [SemanticGate] "
            "开始执行语义补丁检查..."
        )

        reasons = []

        # =====================================================
        # Rule 1
        # 检测逃避式修复 / magic number
        # =====================================================
        suspicious_patterns = [

            r"=\s*11\b",
            r"=\s*20\b",
            r"=\s*999\b",
            r"=\s*9999\b",
            r"=\s*99999\b",
            r"max\s*\(",
            r"min\s*\("
        ]

        for _, code in (
            repo_files.items()
        ):

            for pattern in (
                suspicious_patterns
            ):

                if re.search(
                    pattern,
                    code
                ):

                    reasons.append(
                        "检测到疑似 "
                        "magic number "
                        "或逃避式参数修复"
                    )

                    break

        # =====================================================
        # Rule 2
        # diagnose 提到的文件必须存在
        # （不是“必须修改”）
        # =====================================================
        mentioned_files = set()

        for match in re.findall(
            r"([A-Za-z0-9_]+\.py)",
            analysis
        ):

            mentioned_files.add(
                match.lower()
            )

        repo_file_names = {

            path.lower()
            for path in repo_files.keys()

        }

        for file_name in (
            mentioned_files
        ):

            if (
                file_name
                not in repo_file_names
            ):

                reasons.append(
                    f"诊断涉及 "
                    f"{file_name} "
                    f"但文件不存在"
                )

        # =====================================================
        # Rule 3
        # main.py 不允许删除入口
        # =====================================================
        for path, code in (
            repo_files.items()
        ):

            lower_path = (
                path.lower()
            )

            if (
                lower_path
                == "main.py"
            ):

                if (
                    "__main__"
                    not in code
                ):

                    reasons.append(
                        "疑似删除 "
                        "__main__ "
                        "入口逻辑"
                    )

        # =====================================================
        # Rule 4
        # 空逻辑绕过
        # =====================================================
        suspicious_logic = [

            "pass",
            "return None",
            "return True",
            "return False"
        ]

        for _, code in (
            repo_files.items()
        ):

            for item in (
                suspicious_logic
            ):

                if item in code:

                    reasons.append(
                        "疑似删除逻辑"
                        "或绕过逻辑"
                    )

                    break

        # =====================================================
        # Result
        # =====================================================
        if reasons:

            reason = (
                "；".join(
                    list(
                        set(reasons)
                    )
                )
            )

            print(
                "❌ [SemanticGate] "
                "检查失败"
            )

            print(
                f"原因: {reason}"
            )

            return {
                "passed": False,
                "reason": reason
            }

        print(
            "✅ [SemanticGate] "
            "检查通过"
        )

        return {
            "passed": True,
            "reason": "OK"
        }