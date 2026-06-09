import * as vscode from "vscode";
import { fixCommand } from "./commands/fix";

export function activate(context: vscode.ExtensionContext) {
    // 显式接收并透传 uri 参数
    const disposable = vscode.commands.registerCommand(
        "llm-code-medic.fix",
        (uri?: vscode.Uri) => fixCommand(uri)
    );

    context.subscriptions.push(disposable);
}

export function deactivate() {}