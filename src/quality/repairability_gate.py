from typing import Dict, List, Tuple


class RepairabilityGate:

    def check(self, state: Dict) -> Tuple[bool, str, List[str], bool]:
        print("   [RepairabilityGate] 正在分析修复可行性...")

        analysis = (
            state.get("analysis", "") or ""
        ).upper()

        semantic_reason = (
            state.get("semantic_gate_reason", "") or ""
        ).lower()

        policy_reason = (
            state.get("policy_gate_reason", "") or ""
        ).lower()

        sandbox_stderr = (
            state.get("sandbox_stderr", "") or ""
        ).lower()

        repair_history = "\n".join(
            state.get("repair_history", [])
        ).upper()

        repair_attempts = state.get(
            "repair_attempts",
            0
        )

        options = [
            "允许修改业务输入值（例如调用参数）",
            "允许轻微调整计算公式或阈值",
            "允许增加兼容迁移层（旧接口兼容）",
            "保持严格规则并停止自动修复"
        ]

        reasons = []

        print(
            f"[DEBUG] repair_attempts = {repair_attempts}"
        )
        print(
            f"[DEBUG] sandbox_stderr exists = "
            f"{bool(sandbox_stderr)}"
        )
        print(
            f"[DEBUG] semantic_gate_reason = "
            f"{semantic_reason or 'OK'}"
        )
        print(
            f"[DEBUG] policy_gate_reason = "
            f"{policy_reason}"
        )

        # ==================================================
        # 0. FIRST-ROUND HARD ESCALATION
        # diagnose 已明确判定无法自动修复
        # ==================================================
        hard_escalate = any([
            "ESCALATE_REQUIRED" in analysis,
            "NO_VALID_CALLER_VALUE" in analysis,
            "CALLER_VALUE_NOT_DERIVABLE" in analysis,
            "AUTO_REPAIR_NOT_POSSIBLE" in analysis,
        ])

        if hard_escalate:
            reasons.append(
                "Diagnose 判定当前缺少可推导修复值，必须升级人工决策"
            )

        # ==================================================
        # 1. Diagnose / Repair 主动升级
        # ==================================================
        escalate_detected = (
            "ESCALATE_REQUIRED" in analysis
            or "ESCALATE_REQUIRED" in repair_history
            or "NOTIMPLEMENTEDERROR" in sandbox_stderr.upper()
        )

        if escalate_detected:
            reasons.append(
                "LLM 已明确要求升级（ESCALATE_REQUIRED）"
            )

        # ==================================================
        # 2. Policy Gate 禁止修改 caller input
        # ==================================================
        caller_mutation_blocked = (
            "caller_input_mutation_detected"
            in policy_reason
        )

        if caller_mutation_blocked:
            reasons.append(
                "自动修复尝试修改调用参数，但策略禁止修改业务输入"
            )

        # ==================================================
        # 3. Formula locked
        # ==================================================
        formula_locked = (
            "rule-4" in semantic_reason
            or "公式" in semantic_reason
        )

        if formula_locked:
            reasons.append(
                "计算公式被保护，禁止修改算法逻辑"
            )

        # ==================================================
        # 4. Caller blindspot
        # ==================================================
        caller_blindspot = (
            "rule-6" in semantic_reason
            or "caller" in semantic_reason
        )

        if caller_blindspot:
            reasons.append(
                "检测到调用侧违规，但无法修改调用参数"
            )

        # ==================================================
        # 5. Verify loop detection
        # 保持 >=2，不要改成1
        # ==================================================
        same_error_loop = False

        if repair_attempts >= 2:
            loop_keywords = [
                "zerodivisionerror",
                "valueerror",
                "notimplementederror"
            ]

            same_error_loop = any(
                k in sandbox_stderr
                for k in loop_keywords
            )

        if same_error_loop:
            reasons.append(
                "多轮验证仍为同类异常，疑似不可修复循环"
            )

        # ==================================================
        # Final Decision
        # ==================================================
        if reasons:
            return (
                False,
                "；".join(reasons),
                options,
                True
            )

        return (
            True,
            "当前可继续尝试修复",
            [],
            False
        )