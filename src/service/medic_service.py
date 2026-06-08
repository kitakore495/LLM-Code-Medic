from typing import Dict
from typing import Any
from typing import List
from typing import Optional

from src.engine.medic_engine import MedicEngine


class MedicService:

    def diagnose(
        self,
        repo_root: str,
        error_message: str
    ) -> Dict[str, Any]:

        final_state = (
            MedicEngine(
                repo_root=repo_root
            )
            .run(
                error_message=error_message
            )
        )

        return {
            "success": True,

            "repo_root": repo_root,

            "analysis":
                final_state.get(
                    "analysis",
                    ""
                ),

            "root_cause":
                final_state.get(
                    "root_cause_class",
                    ""
                ),

            "repairable":
                final_state.get(
                    "repairable",
                    True
                ),

            "repairability_reason":
                final_state.get(
                    "repairability_reason",
                    ""
                ),

            "bug_inventory":
                final_state.get(
                    "bug_inventory",
                    ""
                ),

            "modified_files":
                final_state.get(
                    "modified_files",
                    []
                )
        }

    def repair(
        self,
        repo_root: str,
        error_message: str
    ) -> Dict[str, Any]:

        final_state = (
            MedicEngine(
                repo_root=repo_root
            )
            .run(
                error_message=error_message
            )
        )


        print("\n==============================")
        print("FINAL STATE KEYS")
        print("==============================")

        for key in sorted(final_state.keys()):
            print(key)

        print("==============================")
        return {
            "success": True,

            "repo_root": repo_root,

            "is_fixed":
                final_state.get(
                    "is_fixed",
                    False
                ),

            "analysis":
                final_state.get(
                    "analysis",
                    ""
                ),

            "root_cause":
                final_state.get(
                    "root_cause_class",
                    ""
                ),

            "repairable":
                final_state.get(
                    "repairable",
                    True
                ),

            "repairability_reason":
                final_state.get(
                    "repairability_reason",
                    ""
                ),

            "modified_files":
                final_state.get(
                    "modified_files",
                    []
                ),

            "repo_files":
                final_state.get(
                    "repo_files",
                    {}
                ),

            "final_patch":
                final_state.get(
                    "final_patch",
                    ""
                ),

            "verify_passed":
                final_state.get(
                    "verify_passed",
                    False
                )
        }

    def report(
        self,
        repo_root: str,
        error_message: str
    ) -> Dict[str, Any]:

        final_state = (
            MedicEngine(
                repo_root=repo_root
            )
            .run(
                error_message=error_message
            )
        )

        return {
            "success": True,

            "analysis":
                final_state.get(
                    "analysis",
                    ""
                ),

            "root_cause":
                final_state.get(
                    "root_cause_class",
                    ""
                ),

            "bug_inventory":
                final_state.get(
                    "bug_inventory",
                    ""
                ),

            "report_path":
                final_state.get(
                    "report_path",
                    ""
                ),

            "verify_passed":
                final_state.get(
                    "verify_passed",
                    False
                ),

            "patch_quality_passed":
                final_state.get(
                    "patch_quality_passed",
                    False
                ),

            "semantic_gate_passed":
                final_state.get(
                    "semantic_gate_passed",
                    False
                ),

            "policy_gate_passed":
                final_state.get(
                    "policy_gate_passed",
                    False
                )
        }