export interface DiagnoseResponse {

    success: boolean;

    analysis: string;

    root_cause: string;

    repairable: boolean;

    repairability_reason: string;

    bug_inventory: string;
}

export interface RepairResponse {

    success: boolean;

    is_fixed: boolean;

    repairable: boolean;

    analysis: string;

    root_cause: string;

    modified_files: string[];

    verify_passed: boolean;

    final_patch: string;
}

export class MedicClient {

    private readonly baseUrl =
        "http://127.0.0.1:8000";

    async diagnose(
        repoRoot: string,
        errorMessage: string
    ): Promise<DiagnoseResponse> {

        const response =
            await fetch(
                `${this.baseUrl}/diagnose`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        repo_root: repoRoot,
                        error_message: errorMessage
                    })
                }
            );

        if (!response.ok) {

            throw new Error(
                `Diagnose API Error: ${response.status}`
            );
        }

        const result =
            await response.json();

        return result as DiagnoseResponse;
    }

    async repair(
        repoRoot: string,
        errorMessage: string
    ): Promise<RepairResponse> {

        const response =
            await fetch(
                `${this.baseUrl}/repair`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        repo_root: repoRoot,
                        error_message: errorMessage
                    })
                }
            );

        if (!response.ok) {

            throw new Error(
                `Repair API Error: ${response.status}`
            );
        }

        const result =
            await response.json();

        return result as RepairResponse;
    }
}