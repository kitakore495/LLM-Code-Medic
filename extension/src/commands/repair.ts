import * as vscode from "vscode";

import {
    MedicClient
} from "../medicClient";

export async function repairCommand() {

    const workspace =
        vscode.workspace
            .workspaceFolders?.[0];

    if (!workspace) {

        vscode.window.showErrorMessage(
            "No workspace opened."
        );

        return;
    }

    const errorMessage =
        await vscode.window.showInputBox({
            prompt:
                "Paste traceback here"
        });

    if (!errorMessage) {
        return;
    }

    const client =
        new MedicClient();

    try {

        const result =
            await client.repair(
                workspace.uri.fsPath,
                errorMessage
            );

        vscode.window.showInformationMessage(
            `Fixed = ${result.is_fixed}`
        );
    }
    catch (error) {

        vscode.window.showErrorMessage(
            String(error)
        );
    }
}