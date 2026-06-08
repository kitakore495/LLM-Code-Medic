from pydantic import BaseModel
from typing import List
from typing import Dict
from typing import Any


class RepairResponse(BaseModel):

    success: bool

    is_fixed: bool

    repairable: bool

    analysis: str

    root_cause: str

    modified_files: List[str]

    verify_passed: bool

    final_patch: str


class DiagnoseResponse(BaseModel):

    success: bool

    analysis: str

    root_cause: str

    repairable: bool

    repairability_reason: str

    bug_inventory: str