"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.repairCommand = repairCommand;
const vscode = __importStar(require("vscode"));
const medicClient_1 = require("../medicClient");
async function repairCommand() {
    const workspace = vscode.workspace
        .workspaceFolders?.[0];
    if (!workspace) {
        vscode.window.showErrorMessage("No workspace opened.");
        return;
    }
    const errorMessage = await vscode.window.showInputBox({
        prompt: "Paste traceback here"
    });
    if (!errorMessage) {
        return;
    }
    const client = new medicClient_1.MedicClient();
    try {
        const result = await client.repair(workspace.uri.fsPath, errorMessage);
        vscode.window.showInformationMessage(`Fixed = ${result.is_fixed}`);
    }
    catch (error) {
        vscode.window.showErrorMessage(String(error));
    }
}
//# sourceMappingURL=repair.js.map