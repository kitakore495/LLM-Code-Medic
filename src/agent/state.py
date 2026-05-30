from typing import TypedDict
from typing import Dict
from typing import List


class AgentState(TypedDict):

    repo_root: str
    project_map: str
    error_message: str

    target_files: List[str]

    repo_files: Dict[str, str]
    original_repo_files: Dict[str, str]

    repair_attempts: int
    is_fixed: bool

    analysis: str

    # Sandbox
    sandbox_stdout: str
    sandbox_stderr: str

    # Gates
    patch_quality_passed: bool
    patch_quality_reason: str

    semantic_gate_passed: bool
    semantic_gate_reason: str

    policy_gate_passed: bool
    policy_gate_reason: str

    # ==================== 新增：Repairability Gate ====================
    repairable: bool
    repairability_reason: str
    repair_options: List[str]
    needs_user_decision: bool
    repair_status: str