# repairability_gate.py
from typing import Dict, List, Tuple, Literal

# 修复模式类型
RepairMode = Literal["STRICT", "GUIDED", "OVERRIDE"]


class RepairabilityGate:

    def check(
        self,
        state: Dict
    ) -> Tuple[bool, str, List[str], bool]:

        print("   [RepairabilityGate] 正在分析修复可行性...")

        analysis = (state.get("analysis", "") or "").upper()
        semantic_reason = (state.get("semantic_gate_reason", "") or "").lower()
        policy_reason = (state.get("policy_gate_reason", "") or "").lower()
        sandbox_stderr = (state.get("sandbox_stderr", "") or "").lower()
        repair_history = state.get("repair_history", [])
        repair_attempts = state.get("repair_attempts", 0)
        bug_inventory = state.get("bug_inventory", "")

        print(f"[DEBUG] repair_attempts = {repair_attempts}")
        print(f"[DEBUG] sandbox_stderr exists = {bool(sandbox_stderr)}")
        print(f"[DEBUG] semantic_gate_reason = {semantic_reason or 'OK'}")
        print(f"[DEBUG] policy_gate_reason = {policy_reason}")

        reasons = []

        # ── 0. Diagnose 主动升级 ──────────────────────────────
        hard_escalate = any([
            "ESCALATE_REQUIRED" in analysis,
            "NO_VALID_CALLER_VALUE" in analysis,
            "CALLER_VALUE_NOT_DERIVABLE" in analysis,
            "AUTO_REPAIR_NOT_POSSIBLE" in analysis,
        ])
        if hard_escalate:
            reasons.append("Diagnose 判定缺少可推导修复值，需要业务侧提供依据")

        escalate_detected = (
            "ESCALATE_REQUIRED" in analysis
            or "ESCALATE_REQUIRED" in "\n".join(repair_history)
            or "notimplementederror" in sandbox_stderr
        )
        if escalate_detected:
            reasons.append("LLM 已明确要求升级（ESCALATE_REQUIRED）")

        # ── 1. Policy Gate 禁止修改 caller input ────────────────
        caller_mutation_blocked = (
            "caller_input_mutation_detected" in policy_reason
        )
        if caller_mutation_blocked:
            reasons.append("策略禁止修改业务输入参数")

        # ── 2. Formula locked ────────────────────────────────
        formula_locked = (
            "rule-4" in semantic_reason
            or "公式" in semantic_reason
        )
        if formula_locked:
            reasons.append("计算公式受保护，禁止修改算法逻辑")

        # ── 3. Caller blindspot ───────────────────────────────
        caller_blindspot = (
            "rule-6" in semantic_reason
            or "caller 盲区" in semantic_reason
        )
        if caller_blindspot:
            reasons.append("检测到调用侧违规，但 caller 无法推导合法参数值")

        # ── 4. Verify loop（最近3轮同类 signature）─────────────
        # 初始化 signature 历史
        if "error_signature_history" not in state:
            state["error_signature_history"] = []

        current_signature = ""
        # 尝试从 sandbox stderr 中抓取错误类型+文件
        # 格式: TypeError@services/order_service.py
        import re
        stderr_lines = (state.get("sandbox_stderr", "") or "").splitlines()
        for line in stderr_lines:
            match = re.search(r"(attributeerror|typeerror|valueerror|importerror|zerodivisionerror|notimplementederror).*?([a-zA-Z0-9_/]+\.py)", line, re.IGNORECASE)
            if match:
                err_type = match.group(1).lower()
                file_path = match.group(2).replace("\\", "/")
                current_signature = f"{err_type}@{file_path}"
                break

        if current_signature:
            history = state["error_signature_history"]
            history.append(current_signature)
            state["error_signature_history"] = history[-5:]  # 只保留最近5条

            # 最近3轮是否完全相同
            if len(history) >= 3 and all(s == current_signature for s in history[-3:]):
                reasons.append(f"最近3轮均出现同一异常 signature: {current_signature}")

        # ── Final Decision ────────────────────────────────────
        if reasons:
            return False, "；".join(reasons), state.get("error_signature_history", []), True

        return True, "当前可继续尝试修复", state.get("error_signature_history", []), False


# =============================================================================
# 分层授权交互（CLI 阶段）
# VSCode 插件阶段替换为 LangGraph interrupt + 前端 UI
# =============================================================================

# 每个选项对应的修复模式和注入到 AgentState 的授权信息
_AUTHORIZATION_OPTIONS = [
    {
        "label": "提供业务说明并继续修复",
        "mode": "GUIDED",
        "description": (
            "系统无法自动判断正确的参数值，需要你提供业务依据。\n"
            "请说明：这个参数在你的项目里应该是什么值，以及为什么。\n"
            "例如：\n"
            "  - '这个函数要求传入的数量必须大于零，因为它是库存数'\n"
            "  - '超时时间应该是 30 秒，这是我们和第三方约定的'\n"
            "  - '这里应该调用 process()，旧的 run() 接口已经废弃了'\n"
            "系统会根据你的说明，在不违反其他规则的前提下完成修复。"
        ),
        "prompt": "请描述正确的业务逻辑（用自己的话说明参数应该是什么、为什么）：",
    },
    {
        "label": "我知道风险，允许系统灵活处理",
        "mode": "OVERRIDE",
        "description": (
            "系统检测到此问题在严格模式下无法自动修复。\n"
            "如果你了解代码逻辑并确认可以接受灵活处理，请在此授权。\n"
            "你需要说明：允许系统做什么，以及理由是什么。\n"
            "例如：\n"
            "  - '允许调整这个判断条件，因为原来的逻辑写错了'\n"
            "  - '允许增加一个过渡接口，项目正在迁移旧代码'\n"
            "注意：即使授权，以下情况仍会被拒绝：\n"
            "  - 直接返回假数据来掩盖错误\n"
            "  - 捕获异常后不处理、假装没出错"
        ),
        "prompt": "请说明你的授权理由，以及允许系统做什么：",
    },
    {
        "label": "停止修复，我来手动处理",
        "mode": None,
        "description": "终止自动修复流程，系统会输出当前的诊断结果供你参考。",
        "prompt": None,
    },
]

def prompt_user_authorization(
    unrepairable_reason: str,
    analysis: str,
) -> Tuple[bool, RepairMode, str]:
    """CLI 交互层：当 RepairabilityGate 判定不可修复时，向用户展示选项并收集授权"""
    print("\n" + "=" * 60)
    print("🛑  自动修复已终止（需人工决策）")
    print("=" * 60)
    print(f"\n终止原因：{unrepairable_reason}\n")

    _print_diagnosis_summary(analysis)

    print("\n请选择后续操作：\n")
    for i, opt in enumerate(_AUTHORIZATION_OPTIONS, 1):
        print(f"  [{i}] {opt['label']}")
        print(f"      {opt['description'].splitlines()[0]}")
    print()

    while True:
        try:
            choice_str = input("请输入选项编号 (1-3)：").strip()
            choice = int(choice_str)
            if 1 <= choice <= len(_AUTHORIZATION_OPTIONS):
                break
            print(f"  请输入 1 到 {len(_AUTHORIZATION_OPTIONS)} 之间的数字")
        except (ValueError, EOFError):
            print("  输入无效，请重试")

    selected = _AUTHORIZATION_OPTIONS[choice - 1]

    if selected["mode"] is None:
        print("\n✅ 已记录，修复流程终止。")
        return False, "STRICT", ""

    print(f"\n{selected['description']}\n")

    auth_context = ""
    if selected["prompt"]:
        while True:
            auth_context = input(selected["prompt"]).strip()
            if auth_context:
                break
            print("  授权上下文不能为空，请重新输入")

    mode: RepairMode = selected["mode"]
    print(f"\n✅ 已记录授权，切换到 {mode} 模式继续修复。\n")

    return True, mode, auth_context


def _print_diagnosis_summary(analysis: str) -> None:
    """从 analysis 里提取关键字段打印，避免全文转储"""
    import re
    keywords = [
        "ROOT_CAUSE_CLASS",
        "ROOT_CAUSE_LAYER",
        "REPAIR_SCOPE",
        "ESCALATE_REQUIRED",
        "LOOP_VERDICT",
        "BUG_INVENTORY",
    ]
    print("── 诊断摘要 " + "─" * 48)
    found = False
    for line in analysis.splitlines():
        for kw in keywords:
            if kw in line.upper():
                print(f"  {line.strip()}")
                found = True
                break
    if not found:
        print(f"  {analysis[:300]}...")
    print("─" * 60)

def build_authorization_context(
    state: dict
) -> str:
    """
    根据 repair_mode
    动态注入授权上下文。

    STRICT:
        不改变任何行为

    GUIDED:
        用户提供业务依据，
        允许有限 caller correction

    OVERRIDE:
        用户显式授权突破部分 gate
    """

    mode = state.get(
        "repair_mode",
        "STRICT"
    )

    auth_context = (
        state.get(
            "user_authorization",
            ""
        )
        .strip()
    )

    # =====================================================
    # STRICT
    # =====================================================
    if (
        mode == "STRICT"
        or not auth_context
    ):
        return ""

    # =====================================================
    # GUIDED
    # =====================================================
    if mode == "GUIDED":

        return f"""
========================
【用户授权业务上下文 — GUIDED 模式】
========================

用户提供如下业务依据：

{auth_context}

基于此授权：

允许：

- 有限 caller correction
- 修改 caller 参数值
- caller contract alignment

限制：

- 修正值必须与用户说明一致
- 不得发明新的业务值
- 不得超出用户授权范围

仍然禁止：

- 数据伪造
（例如除零路径直接 return 数值）

- 异常吞噬
（except 无 re-raise）

- 修改计算公式

- 修改核心阈值

- 无依据 magic number

如果无法依据用户说明推导修复值：

输出：

ESCALATE_REQUIRED
========================
""".strip()

    # =====================================================
    # OVERRIDE
    # =====================================================
    if mode == "OVERRIDE":

        return f"""
========================
【用户授权例外修复 — OVERRIDE 模式】
========================

用户明确授权：

{auth_context}

允许：

- compatibility shim

- caller correction

- 有依据的 threshold adjustment

约束：

- 必须与用户授权一致

- 必须在代码注释中说明：

# OVERRIDE: <reason>

永远禁止：

- 数据伪造

- 异常吞噬

- 为过测试而引入 magic number

- 无依据业务值

- silent fallback

若修复超出授权范围：

输出：

ESCALATE_REQUIRED
========================
""".strip()

    return ""