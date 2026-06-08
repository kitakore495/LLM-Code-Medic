"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MedicClient = void 0;
class MedicClient {
    constructor() {
        this.baseUrl = "http://127.0.0.1:8000";
    }
    async diagnose(repoRoot, errorMessage) {
        const response = await fetch(`${this.baseUrl}/diagnose`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                repo_root: repoRoot,
                error_message: errorMessage
            })
        });
        if (!response.ok) {
            throw new Error(`Diagnose API Error: ${response.status}`);
        }
        const result = await response.json();
        return result;
    }
    async repair(repoRoot, errorMessage) {
        const response = await fetch(`${this.baseUrl}/repair`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                repo_root: repoRoot,
                error_message: errorMessage
            })
        });
        if (!response.ok) {
            throw new Error(`Repair API Error: ${response.status}`);
        }
        const result = await response.json();
        return result;
    }
}
exports.MedicClient = MedicClient;
//# sourceMappingURL=medicClient.js.map