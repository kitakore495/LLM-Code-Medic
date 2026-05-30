import ast

FORBIDDEN_VAR_NAMES = {
    "weight", "threshold", "timeout", "batch_size", 
    "retry", "count", "limit", "size", "port",
}

def _collect_assignments(code: str):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {}

    result = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        try:
            value = ast.literal_eval(node.value)
            result[target.id] = value
        except Exception:
            continue
    return result

def run_policy_gate(original_repo_files, repaired_repo_files):
    violations = []
    for path, repaired_code in repaired_repo_files.items():
        if path not in original_repo_files:
            continue
        original_code = original_repo_files[path]
        old_assignments = _collect_assignments(original_code)
        new_assignments = _collect_assignments(repaired_code)

        for name, old_value in old_assignments.items():
            if name not in new_assignments or old_value == new_assignments[name]:
                continue
            
            if any(k in name.lower() for k in FORBIDDEN_VAR_NAMES):
                violations.append(f"{path}: {name} {old_value} -> {new_assignments[name]}")

    if violations:
        return False, "CALLER_INPUT_MUTATION_DETECTED\n" + "\n".join(violations)
    return True, ""