import json
import os
from datetime import datetime

class ReportGenerator:

    @staticmethod
    def generate(state):
        report = {
            "timestamp":
                datetime.now().isoformat(),
            "status":
                (
                    "FIXED"
                    if state.get(
                        "is_fixed",
                        False
                    )
                    else "FAILED"
                ),
            "repair_attempts":
                state.get(
                    "repair_attempts",
                    0
                ),
            "error_message":
                state.get(
                    "error_message",
                    ""
                ),
            "analysis":
                state.get(
                    "analysis",
                    ""
                ),
            "target_files":
                state.get(
                    "target_files",
                    []
                ),
            "verify_passed":
                state.get(
                    "verify_passed",
                    False
                ),
            "semantic_gate_passed":
                state.get(
                    "semantic_gate_passed",
                    False
                ),
            "semantic_gate_reason":
                state.get(
                    "semantic_gate_reason",
                    ""
                ),
            "policy_gate_passed":
                state.get(
                    "policy_gate_passed",
                    False
                ),
            "policy_gate_reason":
                state.get(
                    "policy_gate_reason",
                    ""
                ),
            "patch_quality_passed":
                state.get(
                    "patch_quality_passed",
                    False
                ),
            "patch_quality_reason":
                state.get(
                    "patch_quality_reason",
                    ""
                ),
            "sandbox_stdout":
                state.get(
                    "sandbox_stdout",
                    ""
                ),
            "sandbox_stderr":
                state.get(
                    "sandbox_stderr",
                    ""
                ),
            "repair_history":
                state.get(
                    "repair_history",
                    []
                ),
        }
        return report

    @staticmethod
    def to_markdown(report):
        target_files = "\n".join(
            [
                f"- {path}"
                for path in report.get(
                    "target_files",
                    []
                )
            ]
        )

        repair_history = "\n\n".join(
            report.get(
                "repair_history",
                []
            )
        )

        md = f"""
Auto Repair Report
Status
{report["status"]}
Timestamp
{report["timestamp"]}
Repair Attempts
{report["repair_attempts"]}
Error Message
{report["error_message"]}
Analysis
{report["analysis"]}
Target Files
{target_files}
Verify
{report["verify_passed"]}
Patch Quality Gate
PASS = {report["patch_quality_passed"]}
{report["patch_quality_reason"]}
Semantic Gate
PASS = {report["semantic_gate_passed"]}
{report["semantic_gate_reason"]}
Policy Gate
PASS = {report["policy_gate_passed"]}
{report["policy_gate_reason"]}
Sandbox Stdout
{report["sandbox_stdout"]}
Sandbox Stderr
{report["sandbox_stderr"]}
Repair History
{repair_history}
"""
        return md

    @staticmethod
    def save(report):

        report_dir = "output"

        os.makedirs(
            report_dir,
            exist_ok=True
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        json_path = os.path.join(
            report_dir,
            f"report_{timestamp}.json"
        )

        md_path = os.path.join(
            report_dir,
            f"report_{timestamp}.md"
        )

        with open(
            json_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                report,
                f,
                ensure_ascii=False,
                indent=2
            )

        with open(
            md_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                ReportGenerator.to_markdown(
                    report
                )
            )

        return {
            "json": json_path,
            "markdown": md_path,
        }