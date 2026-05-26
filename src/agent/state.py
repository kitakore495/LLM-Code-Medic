from typing import TypedDict
from typing import Dict
from typing import List
from typing import Optional


class AgentState(
    TypedDict
):

    # =====================================================
    # Repo
    # =====================================================
    repo_files: Dict[
        str,
        str
    ]

    ast_map: Dict

    target_files: List[
        str
    ]

    entry_file: str

    # =====================================================
    # Diagnose
    # =====================================================
    analysis: str

    # =====================================================
    # Repair
    # =====================================================
    patch: str

    repair_round: int

    # =====================================================
    # Verify
    # =====================================================
    verification_passed: bool

    verification_output: str

    # =====================================================
    # Patch Quality Gate
    # =====================================================
    patch_gate_passed: bool

    patch_gate_reason: str

    # =====================================================
    # Semantic Patch Gate
    # =====================================================
    semantic_gate_passed: bool

    semantic_gate_reason: str

    # =====================================================
    # Runtime
    # =====================================================
    done: bool