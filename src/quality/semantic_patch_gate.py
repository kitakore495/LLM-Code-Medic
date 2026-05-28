import re
from typing import Dict, List, Tuple

class SemanticPatchGate:
    def check(
        self,
        repo_files: Dict[str, str],
        original_repo_files: Dict[str, str],
        analysis: str,
        target_files: List[str] = None
    ) -> Tuple[bool, str]:

        print("\n🧠 [SemanticGate] 开始执行语义补丁检查 (优化版)...")
        reasons = []
        target_files = target_files or []

        # 1. 拦截定义：明确的逃避型伪代码
        suspicious_patterns = [
            r"except\s*:\s*pass",               # 掩盖错误
            r"if\s+.*:\s*return\s+(None|True|1|0)\b", # 强行返回固定值
            r"adjusted_weight\s*=\s*\d+",      # 硬编码修正权重
        ]

        files_to_check = target_files if target_files else repo_files.keys()

        for path in files_to_check:
            old_code = original_repo_files.get(path, "")
            new_code = repo_files.get(path, "")

            # 只针对修改的部分进行检测
            if old_code == new_code:
                continue

            # 2. 检查每一行，防止误伤合法逻辑
            for line in new_code.splitlines():
                for pattern in suspicious_patterns:
                    if re.search(pattern, line.strip()):
                        reasons.append(f"{path} 发现逃避式补丁: '{line.strip()}'")

        # 3. 检查文件修改完整性
        changed_files = {path.lower() for path in files_to_check 
                         if original_repo_files.get(path) != repo_files.get(path)}
        
        for file_name in target_files:
            if file_name.lower() not in changed_files:
                reasons.append(f"{file_name} 被要求修复但未发生代码变更")

        if reasons:
            reason_str = "；".join(reasons)
            print(f"❌ [SemanticGate] 检查失败: {reason_str}")
            return False, reason_str

        print("✅ [SemanticGate] 检查通过")
        return True, "OK"