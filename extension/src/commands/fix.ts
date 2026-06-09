import * as vscode from 'vscode';
import { MedicClient } from '../medicClient';

export async function fixCommand(uri?: vscode.Uri) {
    let repoRoot: string; // 保持原有变量名，不新增任何额外字段

    if (uri && uri.fsPath) {
        // 右键菜单触发：直接拿当前选中的绝对路径（不追溯父文件夹）
        repoRoot = uri.fsPath;
    } else {
        // 命令面板/降级触发：直接拿当前编辑器的文件绝对路径（不追溯父文件夹）
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage("请右键点击文件/文件夹执行修复，或先打开一个代码文件");
            return;
        }
        repoRoot = editor.document.uri.fsPath;
    }

    // 提示当前发送给后端的真实路径
    vscode.window.showInformationMessage(`LLM Code Medic 正在修复: ${repoRoot}`);

    try {
        const client = new MedicClient();
        // 依旧只传递 repoRoot 和错误信息，接口完全不改变
        const result = await client.repair(repoRoot, "Auto Repair");
        if (result.is_fixed) {
            const outputPath = result.output_dir || "D:\\python project\\LLM Code Medic\\output";
            vscode.window.showInformationMessage(`修复成功\n修改文件数: ${result.modified_files.length}`, "打开输出目录").then(selection => {
                if (selection === "打开输出目录") {
                    vscode.commands.executeCommand("revealFileInOS", vscode.Uri.file(outputPath));
                }
            });
        } else {
            vscode.window.showWarningMessage(result.root_cause || "修复未完成");
        }
    } catch (error) {
        vscode.window.showErrorMessage(String(error));
    }
}