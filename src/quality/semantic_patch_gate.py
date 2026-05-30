import ast
import re
from typing import Dict, List, Tuple


class SemanticPatchGate:
    """
    语义补丁门禁。
    检测以下修复反模式：
      RULE-1  除数为零路径 return 数值（数据伪造）
      RULE-2  异常吞噬（except 块无 re-raise）
      RULE-3  无 DeprecationWarning 的 shim
      RULE-4  已有函数内公式常量被移除或替换
      RULE-5  已有函数签名参数数量变化
      RULE-6  Caller 盲区（callee 契约已存在但 caller 未被修复）
      RULE-7  target_files 必须有实际修改（智能协同版）
    """

    # =========================================================
    # RULE-1
    # =========================================================
    @staticmethod
    def _check_division_magic_returns(path: str, new_tree: ast.AST) -> List[str]:
        hits = []
        for func in ast.walk(new_tree):
            if not isinstance(func, ast.FunctionDef):
                continue
            has_division = any(
                isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div)
                for n in ast.walk(func)
            )
            if not has_division:
                continue
            for node in ast.walk(func):
                if not isinstance(node, ast.If):
                    continue
                test = node.test
                is_zero_guard = (
                    isinstance(test, ast.Compare)
                    and any(
                        isinstance(c, ast.Constant) and c.value == 0
                        for c in test.comparators
                    )
                )
                if not is_zero_guard:
                    continue
                for stmt in ast.walk(node):
                    if not isinstance(stmt, ast.Return):
                        continue
                    val = stmt.value
                    if val is not None and isinstance(val, (ast.BinOp, ast.Constant)):
                        hits.append(
                            f"{path}:{func.name} "
                            f"RULE-1 数据伪造：除数为零分支 return 数值表达式而非 raise"
                        )
        return hits

    # =========================================================
    # RULE-2
    # =========================================================
    @staticmethod
    def _check_swallowed_exceptions(path: str, new_tree: ast.AST) -> List[str]:
        hits = []
        for node in ast.walk(new_tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            has_raise = any(isinstance(child, ast.Raise) for child in ast.walk(node))
            if not has_raise:
                hits.append(
                    f"{path}:line {node.lineno} "
                    f"RULE-2 异常吞噬：except 块无 re-raise 或 escalate"
                )
        return hits

    # =========================================================
    # RULE-3
    # =========================================================
    @staticmethod
    def _check_undocumented_shims(
        path: str,
        old_funcs: Dict[str, ast.FunctionDef],
        new_funcs: Dict[str, ast.FunctionDef],
    ) -> List[str]:
        hits = []
        existing = set(old_funcs.keys())
        for func_name, func_node in new_funcs.items():
            if func_name in existing:
                continue
            if not func_node.args.defaults:
                continue
            calls_existing = any(
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id in existing
                for n in ast.walk(func_node)
            )
            if not calls_existing:
                continue
            has_deprecation = any(
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "warn"
                for n in ast.walk(func_node)
            )
            if not has_deprecation:
                hits.append(
                    f"{path}:{func_name} "
                    f"RULE-3 隐式 shim：新增函数含默认参数且转发已有函数，缺少 DeprecationWarning"
                )
        return hits

    # =========================================================
    # RULE-4
    # 检测已有函数内的公式数值是否被篡改。
    # =========================================================
    @staticmethod
    def _check_formula_mutations(
        path: str,
        old_funcs: Dict[str, ast.FunctionDef],
        new_funcs: Dict[str, ast.FunctionDef],
        new_tree: ast.AST,
    ) -> List[str]:
        hits = []

        module_consts: Dict[str, float] = {}
        for node in ast.walk(new_tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and (target.id.startswith('_') or target.id.isupper())
                        and isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, (int, float))
                    ):
                        module_consts[target.id] = node.value.value

        def binop_resolved_values(func_node: ast.FunctionDef) -> set:
            result = set()
            for node in ast.walk(func_node):
                if isinstance(node, ast.BinOp):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Constant) and isinstance(child.value, (int, float)):
                            result.add(child.value)
                        elif isinstance(child, ast.Name) and child.id in module_consts:
                            result.add(module_consts[child.id])
            return result

        def binop_raw_constants(func_node: ast.FunctionDef) -> set:
            result = set()
            for node in ast.walk(func_node):
                if isinstance(node, ast.BinOp):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Constant) and isinstance(child.value, (int, float)):
                            result.add(child.value)
            return result

        for func_name in old_funcs:
            if func_name not in new_funcs:
                continue
            old_vals = binop_raw_constants(old_funcs[func_name])
            new_vals = binop_resolved_values(new_funcs[func_name])
            removed = old_vals - new_vals
            if removed:
                hits.append(
                    f"{path}:{func_name} "
                    f"RULE-4 公式数值被移除或替换: {removed}。"
                    f"（将字面量提取为具名常量是允许的，但数值本身不能改变）"
                )
        return hits

    # =========================================================
    # RULE-5
    # =========================================================
    @staticmethod
    def _check_signature_drift(
        path: str,
        old_funcs: Dict[str, ast.FunctionDef],
        new_funcs: Dict[str, ast.FunctionDef],
    ) -> List[str]:
        hits = []
        for func_name in old_funcs:
            if func_name not in new_funcs:
                continue
            old_argc = len(old_funcs[func_name].args.args)
            new_argc = len(new_funcs[func_name].args.args)
            if old_argc != new_argc:
                hits.append(
                    f"{path}:{func_name} "
                    f"RULE-5 签名漂移：参数数量 {old_argc} → {new_argc}"
                )
        return hits

    # =========================================================
    # RULE-6: Caller 盲区检测
    # =========================================================
    @staticmethod
    def _check_caller_blindspot(
        repo_files: Dict[str, str],
        original_repo_files: Dict[str, str],
        target_files: List[str],
        sandbox_stderr: str,
    ) -> List[str]:
        hits = []
        if not sandbox_stderr:
            return hits

        if not re.search(r"\b\w*Error\b|\braise\b", sandbox_stderr):
            return hits

        pure_callee_files: List[str] = []
        for tf in target_files:
            original_code = original_repo_files.get(tf, "")
            repaired_code = repo_files.get(tf, "")
            if repaired_code == original_code:
                continue
            original_had_raise = bool(re.search(r"\braise\b", original_code))
            repaired_has_raise = bool(re.search(r"\braise\b", repaired_code))
            if repaired_has_raise and not original_had_raise:
                pure_callee_files.append(tf)

        if not pure_callee_files:
            return hits

        callee_func_names: set = set()
        for tf in pure_callee_files:
            code = repo_files.get(tf, "")
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        callee_func_names.add(node.name)
            except SyntaxError:
                pass

        if not callee_func_names:
            return hits

        unmodified_callers: List[str] = []
        for repo_path, repaired_code in repo_files.items():
            if repo_path in pure_callee_files:
                continue

            original_code = original_repo_files.get(repo_path, "")
            if repaired_code != original_code:
                continue

            try:
                tree = ast.parse(repaired_code)
            except SyntaxError:
                continue

            calls_callee = any(
                (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in callee_func_names
                ) or (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in callee_func_names
                )
                for node in ast.walk(tree)
            )

            if calls_callee:
                unmodified_callers.append(repo_path)

        if unmodified_callers:
            hits.append(
                f"RULE-6 Caller 盲区：本轮为 callee {pure_callee_files} 新增了 raise 契约，"
                f"但 sandbox 仍然失败（stderr 含异常），"
                f"且以下 caller 文件本轮未被修改：{unmodified_callers}。"
                f"诊断必须将 ROOT_CAUSE_CLASS 重新评估为 [CALLER_VIOLATED]，"
                f"并将上述 caller 文件纳入 TARGET_FILES。"
            )

        return hits

    # =========================================================
    # Entry
    # =========================================================
    def check(
        self,
        repo_files: Dict[str, str],
        original_repo_files: Dict[str, str],
        analysis: str,
        target_files: List[str] = None,
        sandbox_stderr: str = "",
    ) -> Tuple[bool, str]:

        print("\n🧠 [SemanticGate] 开始执行语义补丁检查 (AST增强版)...")

        reasons: List[str] = []
        target_files = target_files or []
        files_to_check = target_files if target_files else list(repo_files.keys())

        # ── Rule 0: Regex 快速拦截 ──────────────────────────────
        dangerous_patterns = [
            (r"except\s*:\s*pass", "裸 except:pass 吞噬一切异常"),
            (r"^\s*adjusted_weight\s*=\s*\d+\s*$", "adjusted_weight 被硬编码为字面量"),
        ]
        for path in files_to_check:
            old_code = original_repo_files.get(path, "")
            new_code = repo_files.get(path, "")
            if old_code == new_code:
                continue
            for lineno, line in enumerate(new_code.splitlines(), 1):
                stripped = line.strip()
                for pattern, label in dangerous_patterns:
                    if re.search(pattern, stripped):
                        reasons.append(f"{path}:{lineno} Rule-0 {label}: '{stripped}'")

        # ── AST 规则 Rule 1-5 ───────────────────────────────────
        for path in files_to_check:
            old_code = original_repo_files.get(path, "")
            new_code = repo_files.get(path, "")
            if old_code == new_code:
                continue
            try:
                old_tree = ast.parse(old_code)
                new_tree = ast.parse(new_code)
            except SyntaxError as e:
                reasons.append(f"{path} 语法错误，无法解析: {e}")
                continue

            old_funcs = {
                n.name: n for n in ast.walk(old_tree) if isinstance(n, ast.FunctionDef)
            }
            new_funcs = {
                n.name: n for n in ast.walk(new_tree) if isinstance(n, ast.FunctionDef)
            }

            reasons.extend(self._check_division_magic_returns(path, new_tree))
            reasons.extend(self._check_swallowed_exceptions(path, new_tree))
            reasons.extend(self._check_undocumented_shims(path, old_funcs, new_funcs))
            reasons.extend(self._check_formula_mutations(path, old_funcs, new_funcs, new_tree))
            reasons.extend(self._check_signature_drift(path, old_funcs, new_funcs))

        # ── RULE-6: Caller 盲区（跨文件，仅在有 stderr 时触发）──
        if sandbox_stderr:
            rule6_hits = self._check_caller_blindspot(
                repo_files=repo_files,
                original_repo_files=original_repo_files,
                target_files=target_files,
                sandbox_stderr=sandbox_stderr,
            )
            reasons.extend(rule6_hits)

        # ── 💡 升级版 RULE-7: target_files 协同改动判定 ────────────────
        if "NO_FAULT_DETECTED" in analysis or "NO_REPAIR_NEEDED" in analysis:
            print("ℹ️ [SemanticGate] 检测到诊断为无需修复，跳过 RULE-7 强改约束")
        else:
            # 统计当前整批待检查文件中，有哪些文件被真正修改了
            changed_files = {
                p.lower()
                for p in files_to_check
                if original_repo_files.get(p) != repo_files.get(p)
            }
            
            # 如果整批 target_files 里至少有一个文件被成功改动了（协同修复开始奏效）
            # 那么未发生改动的文件将被智能放行，不再做机械的死锁拦截
            if len(changed_files) > 0:
                unchanged_targets = [f for f in target_files if f.lower() not in changed_files]
                if unchanged_targets:
                    print(f"ℹ️ [SemanticGate] 协同修复检测：已修改文件 {list(changed_files)}，智能放行未修改的目标文件: {unchanged_targets}")
            else:
                # 只有在诊断要求修复，且大模型完全一个文件都没改动的情况下，才报 RULE-7
                for file_name in target_files:
                    if file_name.lower() not in changed_files:
                        reasons.append(f"{file_name} RULE-7: 被要求修复但未修改")

        # ── Result ──────────────────────────────────────────────
        if reasons:
            reason_str = "；".join(reasons)
            print("❌ [SemanticGate] 检查失败")
            print(f"原因: {reason_str}")
            return False, reason_str

        print("✅ [SemanticGate] 检查通过")
        return True, "OK"