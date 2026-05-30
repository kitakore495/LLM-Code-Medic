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
      RULE-7  target_files 必须有实际修改
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
    #
    # 关键设计：区分"值被修改"和"值被具名化（提取为常量）"
    #
    # 合规重构（允许）：
    #   旧: adjusted_weight = weight - 10
    #   新: _WEIGHT_ADJUSTMENT = 10
    #       adjusted_weight = weight - _WEIGHT_ADJUSTMENT
    #   → BinOp 里的 Constant(10) 变成了 Name('_WEIGHT_ADJUSTMENT')
    #   → 通过模块级常量表解析后，数值集合不变，不触发
    #
    # 违规篡改（拒绝）：
    #   旧: adjusted_weight = weight - 10
    #   新: adjusted_weight = weight - 9   ← 数值被改变
    #   → 解析后数值集合 {9} vs {10}，removed={10}，触发
    # =========================================================
    @staticmethod
    def _check_formula_mutations(
        path: str,
        old_funcs: Dict[str, ast.FunctionDef],
        new_funcs: Dict[str, ast.FunctionDef],
        new_tree: ast.AST,
    ) -> List[str]:
        hits = []

        # 提取模块级具名常量表：_NAME = value 或 NAME = value
        # 用于把 BinOp 里的 Name 引用解析回实际数值
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
            """
            收集函数内 BinOp 的数值集合。
            Constant 节点直接取值；Name 节点查模块常量表解析。
            未能解析的 Name（运行时变量）忽略，不参与对比。
            """
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
            """旧函数：只取 Constant，旧代码不会有具名常量引用"""
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
    # RULE-6: Caller 盲区检测（重写版）
    #
    # 设计约束（避免误杀）：
    #   - callee 必须是"仅被调用、自身不调用其他 target_files 函数"的文件
    #     即：在 target_files 内，通过拓扑关系识别真正的 callee
    #   - caller 的判断来源是 repo_files 中非 target_files 的文件
    #     或 target_files 中但本轮未被实际修改的文件
    #   - 如果 caller 已在 target_files 且已被修改：不触发 RULE-6
    #
    # 触发条件（全部满足）：
    #   a) sandbox_stderr 包含明确的异常类名（ValueError、Error 等）
    #   b) 存在"纯 callee 文件"：该文件在修复后包含 raise，
    #      且该文件在原始版本中不包含 raise（即 raise 是本轮新增的）
    #   c) 存在调用了该 callee 函数的文件，且该文件
    #      在 repo_files 中与 original_repo_files 完全相同（未被修改）
    #
    # 条件 c 是关键修正：只要 caller 已经被修改，就不触发 RULE-6。
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

        # 条件 a: stderr 包含异常类名
        if not re.search(r"\b\w*Error\b|\braise\b", sandbox_stderr):
            return hits

        # ── 识别"纯 callee 文件" ──────────────────────────────
        # 定义：在 target_files 中，修复后新增了 raise，
        # 且原始版本没有 raise（说明本轮是"给 callee 加契约"）
        pure_callee_files: List[str] = []
        for tf in target_files:
            original_code = original_repo_files.get(tf, "")
            repaired_code = repo_files.get(tf, "")
            if repaired_code == original_code:
                continue  # 未被修改，不是本轮的 callee
            original_had_raise = bool(re.search(r"\braise\b", original_code))
            repaired_has_raise = bool(re.search(r"\braise\b", repaired_code))
            if repaired_has_raise and not original_had_raise:
                pure_callee_files.append(tf)

        if not pure_callee_files:
            return hits  # 没有"本轮新增 raise 的 callee"，不触发

        # ── 提取 pure_callee_files 中定义的函数名 ──────────────
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

        # ── 找出调用了 callee 函数但本轮未被修改的文件 ────────
        # "未被修改" = repo_files[path] == original_repo_files[path]
        unmodified_callers: List[str] = []
        for repo_path, repaired_code in repo_files.items():
            if repo_path in pure_callee_files:
                continue  # 跳过 callee 自身

            # 关键判断：该文件本轮是否已被修改？
            original_code = original_repo_files.get(repo_path, "")
            if repaired_code != original_code:
                continue  # 已被修改，说明已纳入修复范围，不触发

            # 检查该文件是否调用了 callee 函数
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

        # ── RULE-7: target_files 必须有实际修改 ────────────────
        changed = {
            p.lower()
            for p in files_to_check
            if original_repo_files.get(p) != repo_files.get(p)
        }
        for file_name in target_files:
            if file_name.lower() not in changed:
                reasons.append(f"{file_name} RULE-7: 被要求修复但未修改")

        # ── Result ──────────────────────────────────────────────
        if reasons:
            reason_str = "；".join(reasons)
            print("❌ [SemanticGate] 检查失败")
            print(f"原因: {reason_str}")
            return False, reason_str

        print("✅ [SemanticGate] 检查通过")
        return True, "OK"