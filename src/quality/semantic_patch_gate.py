import ast
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

        print("\n🧠 [SemanticGate] 开始执行语义补丁检查 (AST增强版)...")

        reasons = []
        target_files = target_files or []
        files_to_check = target_files if target_files else list(repo_files.keys())

        # Rule 0: 基础逃避模式
        suspicious_patterns = [
            r"except\s*:\s*pass",
            r"return\s+(None|True|False|1|0)\b",
            r"max\s*\(",
            r"min\s*\(",
        ]

        for path in files_to_check:
            old_code = original_repo_files.get(path, "")
            new_code = repo_files.get(path, "")
            if old_code == new_code:
                continue
            for line in new_code.splitlines():
                stripped = line.strip()
                for pattern in suspicious_patterns:
                    if re.search(pattern, stripped):
                        reasons.append(f"{path} 发现逃避式补丁: '{stripped}'")

        # AST 分析
        for path in files_to_check:
            old_code = original_repo_files.get(path, "")
            new_code = repo_files.get(path, "")
            if old_code == new_code:
                continue

            try:
                old_tree = ast.parse(old_code)
                new_tree = ast.parse(new_code)
            except Exception:
                continue

            # 函数签名与新增函数
            old_funcs = {node.name: node for node in ast.walk(old_tree) if isinstance(node, ast.FunctionDef)}
            new_funcs = {node.name: node for node in ast.walk(new_tree) if isinstance(node, ast.FunctionDef)}

            for func_name in old_funcs:
                if func_name not in new_funcs:
                    continue
                old_f = old_funcs[func_name]
                new_f = new_funcs[func_name]
                if len(new_f.args.args) != len(old_f.args.args):
                    reasons.append(f"{path} 函数签名变化: {func_name}")
                if len(new_f.args.defaults) > len(old_f.args.defaults):
                    reasons.append(f"{path} 新增默认参数: {func_name}")

            # 新增 helper 函数
            injected = set(new_funcs.keys()) - set(old_funcs.keys())
            for name in injected:
                reasons.append(f"{path} 新增 helper 函数: {name}")

            # ==================== 常量定义检测 ====================
            def is_constant_definition(node):
                """判断是否为合法的命名常量定义"""
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            name = target.id
                            if name.startswith('_') or name.isupper():
                                return True
                return False

            def get_inline_magic_numbers(tree):
                numbers = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                        if abs(node.value) <= 1:  # 允许 0,1 等常见小常量
                            continue
                        # 跳过常量定义
                        if any(is_constant_definition(parent) for parent in ast.walk(tree) 
                               if hasattr(parent, 'value') and getattr(parent, 'value', None) is node):
                            continue
                        numbers.add(node.value)
                return numbers

            old_magic = get_inline_magic_numbers(old_tree)
            new_magic = get_inline_magic_numbers(new_tree)

            if new_magic - old_magic:
                reasons.append(f"{path} 新增可疑 magic number（未定义为常量）: {list(new_magic - old_magic)}")

            # 数学表达式保护（允许合理重构）
            def get_math_sigs(tree):
                sigs = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.BinOp):
                        left = node.left.__class__.__name__
                        right = node.right.__class__.__name__
                        op = node.op.__class__.__name__
                        sig = f"BinOp({op}, {left}, {right})"
                        sigs.append(sig)
                return set(sigs)

            old_sigs = get_math_sigs(old_tree)
            new_sigs = get_math_sigs(new_tree)
            if old_sigs and len(new_sigs) < len(old_sigs) - 3:   # 更宽松阈值
                reasons.append(f"{path} 关键数学表达式被大幅修改")

        # Target 文件必须修改
        changed_files = {
            p.lower() for p in files_to_check
            if original_repo_files.get(p) != repo_files.get(p)
        }

        for file_name in target_files:
            if file_name.lower() not in changed_files:
                reasons.append(f"{file_name} 被要求修复但未修改")

        if reasons:
            reason_str = "；".join(reasons)
            print("❌ [SemanticGate] 检查失败")
            print(f"原因: {reason_str}")
            return False, reason_str

        print("✅ [SemanticGate] 检查通过")
        return True, "OK"