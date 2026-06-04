from typing import TypedDict, Dict, List, Literal, Optional

# 定义修复模式类型
RepairMode = Literal["STRICT", "GUIDED", "OVERRIDE"]

class AgentState(TypedDict):
    # 基础路径与元数据
    repo_root: str
    project_map: str
    error_message: str

    # 文件操作相关
    target_files: List[str]
    repo_files: Dict[str, str]
    original_repo_files: Dict[str, str]
    repaired_repo_files: Dict[str, str]  # 防止文件字典丢失

    # 状态控制
    repair_attempts: int
    is_fixed: bool
    analysis: str

    # 沙箱与验证
    sandbox_stdout: str
    sandbox_stderr: str
    verify_passed: bool  # 沙箱是否通过的通行证

    # Gates (质量与策略控制)
    patch_quality_passed: bool
    patch_quality_reason: str

    semantic_gate_passed: bool
    semantic_gate_reason: str

    policy_gate_passed: bool
    policy_gate_reason: str

    # Repairability Gate (修复能力判定)
    repairable: bool
    repairability_reason: str
    repair_options: List[str]
    needs_user_decision: bool
    repair_status: str

    # --- 新增字段：修复模式与授权控制 ---
    repair_mode: str          # "STRICT" | "GUIDED" | "OVERRIDE"
    user_authorization: str   # 用户提供的业务依据
    is_unrepairable: bool     # RepairabilityGate 判定为不可修复时设为 True
    unrepairable_reason: str  # 不可修复的具体原因

    _pending_repair_mode: str
    _pending_authorization: str

    export_table: Dict
    call_graph: Dict
    import_graph: Dict