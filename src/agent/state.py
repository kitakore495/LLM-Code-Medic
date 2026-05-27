from typing import TypedDict
from typing import Dict
from typing import List


class AgentState(TypedDict):

    repo_root: str

    project_map: str

    error_message: str

    target_files: List[str]

    repo_files: Dict[
        str,
        str
    ]

    original_repo_files: Dict[
        str,
        str
    ]

    attempts: int

    repair_attempts: int

    is_fixed: bool

    analysis: str

    # =====================================================
    # Sandbox
    # =====================================================
    sandbox_stdout: str
    sandbox_stderr: str

    # =====================================================
    # Patch Quality Gate
    # =====================================================
    patch_quality_passed: bool
    patch_quality_reason: str

    # =====================================================
    # Semantic Patch Gate
    # =====================================================
    semantic_gate_passed: bool
    semantic_gate_reason: str