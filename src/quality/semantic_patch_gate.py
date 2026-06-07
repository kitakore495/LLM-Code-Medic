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

            body = node.body

            #
            # except:
            #
            if not body:
                hits.append(
                    f"{path}:line {node.lineno} RULE-2 空 except"
                )
                continue

            #
            # except: pass
            #
            if len(body) == 1 and isinstance(body[0], ast.Pass):
                hits.append(
                    f"{path}:line {node.lineno} RULE-2 except: pass"
                )
                continue

            #
            # except: ...
            #
            if (
                len(body) == 1
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and body[0].value.value == Ellipsis
            ):
                hits.append(
                    f"{path}:line {node.lineno} RULE-2 except: ..."
                )
                continue

            #
            # 有任何业务处理直接放行
            #
            has_meaningful_stmt = any(
                isinstance(
                    stmt,
                    (
                        ast.Return,
                        ast.Raise,
                        ast.Assign,
                        ast.AugAssign,
                        ast.Expr,
                        ast.Break,
                        ast.Continue,
                        ast.If,
                        ast.For,
                        ast.While,
                        ast.Try,
                    ),
                )
                for stmt in body
            )

            if has_meaningful_stmt:
                continue

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

        """
        弱提示版本。

        不再阻断 SemanticGate。

        仅给 Diagnose 提示：
        可能存在 Caller Blind Spot。
        """

        hints = []

        if not sandbox_stderr:
            return hints

        changed_files = []

        for path in target_files:

            old_code = original_repo_files.get(path, "")
            new_code = repo_files.get(path, "")

            if old_code != new_code:
                changed_files.append(path)

        if not changed_files:
            return hints

        caller_candidates = []

        for path, code in repo_files.items():

            if path in changed_files:
                continue

            try:
                tree = ast.parse(code)
            except SyntaxError:
                continue

            call_count = sum(
                1
                for n in ast.walk(tree)
                if isinstance(n, ast.Call)
            )

            if call_count > 0:
                caller_candidates.append(path)

        if caller_candidates:

            hints.append(
                "RULE-6(HINT): sandbox仍失败，"
                f"本轮修改文件={changed_files}，"
                f"可能存在未修改caller={caller_candidates[:10]}"
            )

        return hints

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
        bug_inventory: str = "",
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

            rule6_hints = self._check_caller_blindspot(
                repo_files=repo_files,
                original_repo_files=original_repo_files,
                target_files=target_files,
                sandbox_stderr=sandbox_stderr,
            )

            for h in rule6_hints:
                print(f"ℹ️ {h}")

        # ── RULE-7: 极简版 ─────────────────────────────

        if "NO_FAULT_DETECTED" in analysis or "NO_REPAIR_NEEDED" in analysis:

            print(
                "ℹ️ [SemanticGate] 检测到无需修复，跳过 RULE-7"
            )

        else:

            changed_files = {
                p.lower()
                for p in files_to_check
                if original_repo_files.get(p) != repo_files.get(p)
            }

            #
            # 唯一拦截条件：
            # LLM 一行代码都没改
            #
            if not changed_files:

                reasons.append(
                    "RULE-7: LLM 未产生任何实际修改"
                )

            else:

                print(
                    f"ℹ️ [SemanticGate] RULE-7 放行，"
                    f"本轮修改文件数={len(changed_files)}"
                )
        # ── Result ──────────────────────────────────────────────
        if reasons:
            reason_str = "；".join(reasons)
            print("❌ [SemanticGate] 检查失败")
            print(f"原因: {reason_str}")
            return False, reason_str

        print("✅ [SemanticGate] 检查通过")
        return True, "OK"