import * as vscode from "vscode";

import {
    diagnoseCommand
} from "./commands/diagnose";

import {
    repairCommand
} from "./commands/repair";

export function activate(
    context: vscode.ExtensionContext
) {

    const diagnoseDisposable =
        vscode.commands.registerCommand(
            "llm-code-medic.diagnose",
            diagnoseCommand
        );

    const repairDisposable =
        vscode.commands.registerCommand(
            "llm-code-medic.repair",
            repairCommand
        );

    context.subscriptions.push(
        diagnoseDisposable
    );

    context.subscriptions.push(
        repairDisposable
    );
}

export function deactivate() {}