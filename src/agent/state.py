from typing import TypedDict
from typing import Dict
from typing import List


class AgentState(
    TypedDict
):

    # =========================================================
    # Repo Snapshot
    # =========================================================
    repo_files: Dict[
        str,
        str
    ]

    # =========================================================
    # Diagnose
    # =========================================================
    analysis: str

    target_files: List[
        str
    ]

    # =========================================================
    # Repair
    # =========================================================
    repair_attempts: int

    # =========================================================
    # Verify
    # =========================================================
    sandbox_passed: bool

    sandbox_stdout: str

    sandbox_stderr: str

    # =========================================================
    # Patch Quality Gate
    # =========================================================
    patch_quality_passed: bool

    patch_quality_reason: str