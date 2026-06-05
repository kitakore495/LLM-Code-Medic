import os
import ast


class ProjectScanner:

    def __init__(self, repo_root="."):
        self.repo_root = os.path.abspath(repo_root)
        self.ignore_list = {
            ".git", "__pycache__", ".venv",
            "venv", ".pytest_cache", ".vscode"
        }
        self.export_table = {}
        self.import_graph = {}
        self.call_graph = {}

    def _parse_python_file(self, file_path):
        result = {
            "classes": [],
            "functions": [],
            "imports": [],
            "exports": [],
            "calls": []
        }

        # 修复1: 先尝试 utf-8，再 fallback 到 latin-1，避免 encoding 异常吃掉整个文件
        source = None
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    source = f.read()
                break
            except UnicodeDecodeError:
                continue

        if source is None:
            return None

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        # 修复2: classes 扫顶层 ClassDef
        result["classes"] = [
            node.name
            for node in tree.body
            if isinstance(node, ast.ClassDef)
        ]

        # 修复3: functions 扫顶层 FunctionDef
        # 类方法单独收集，放进 exports 但不放进 functions（保持语义区分）
        result["functions"] = [
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef)
        ]

        # 修复4: 收集类方法，加入 exports（原来完全缺失）
        class_methods = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not (item.name.startswith("__") and item.name.endswith("__")):
                            class_methods.append(item.name)

        # imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "type": "import",
                        "module": alias.name,
                        "symbol": None
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append({
                        "type": "from",
                        "module": module,
                        "symbol": alias.name
                    })
        result["imports"] = imports

        # calls
        calls = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            if func_name:
                calls.append(func_name)
        result["calls"] = list(set(calls))

        # exports = 顶层函数 + 顶层类名 + 类方法
        exports = []
        exports.extend(result["functions"])
        exports.extend(result["classes"])
        exports.extend(class_methods)
        result["exports"] = list(set(exports))

        return result

    def _build_file_info(self, parsed_info):
        if not parsed_info:
            return " (parse error)"
        info = []
        all_defs = parsed_info["functions"] + parsed_info["classes"]
        if all_defs:
            info.append("defs: " + ", ".join(all_defs))
        if parsed_info["imports"]:
            info.append(f"imports: {len(parsed_info['imports'])}")
        if parsed_info["calls"]:
            info.append(f"calls: {len(parsed_info['calls'])}")
        return f" ({' | '.join(info)})" if info else ""

    def _build_import_graph(self):
        graph = {}
        for file_path, info in self.export_table.items():
            imports = list(set(
                imp["module"]
                for imp in info["imports"]
                if imp["module"]
            ))
            graph[file_path] = imports
        self.import_graph = graph

    def _build_call_graph(self):
        graph = {}
        all_exports = {}
        for file_path, info in self.export_table.items():
            for symbol in info["exports"]:
                all_exports[symbol] = file_path

        for file_path, info in self.export_table.items():
            called_files = list(set(
                all_exports[call_name]
                for call_name in info["calls"]
                if call_name in all_exports
                and all_exports[call_name] != file_path
            ))
            graph[file_path] = called_files
        self.call_graph = graph

    def scan(self):
        self.export_table = {}
        self.import_graph = {}
        self.call_graph = {}
        tree_lines = []

        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [d for d in dirs if d not in self.ignore_list]

            level = root.replace(self.repo_root, "").count(os.sep)
            indent = " " * 4 * level
            folder_name = os.path.basename(root) or self.repo_root
            tree_lines.append(f"{indent}📂 {folder_name}/")
            sub_indent = " " * 4 * (level + 1)

            for file_name in sorted(files):
                if not file_name.endswith(".py") or file_name == "__init__.py":
                    continue

                full_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(full_path, self.repo_root).replace("\\", "/")

                parsed_info = self._parse_python_file(full_path)

                if parsed_info is not None:
                    self.export_table[rel_path] = parsed_info

                tree_lines.append(
                    f"{sub_indent}📄 {file_name}{self._build_file_info(parsed_info)}"
                )

        self._build_import_graph()
        self._build_call_graph()

        total_exports = sum(len(v["exports"]) for v in self.export_table.values())
        total_symbols = len({
            s for v in self.export_table.values() for s in v["exports"]
        })
        total_calls = sum(
            len(v) for v in self.call_graph.values()
        )
        total_imports = sum(
            len(v) for v in self.import_graph.values()
        )

        print(
            f"📊 ExportTable: {len(self.export_table)}"
            f" 📊 SymbolIndex: {total_symbols}"
            f" 📊 CallGraph: {total_calls}"
            f" 📊 ImportGraph: {total_imports}"
            f" 📊 TotalExports: {total_exports}"
        )

        return {
            "tree": "\n".join(tree_lines),
            "export_table": self.export_table,
            "call_graph": self.call_graph,
            "import_graph": self.import_graph,
        }

    def scan_project(self): return self.scan()
    def get_export_table(self): return self.export_table
    def get_call_graph(self): return self.call_graph
    def get_import_graph(self): return self.import_graph


def scan_in_memory(repo_files: dict):
    """
    接收内存中的源码快照字典 {rel_path: source_code_string}
    返回与 ProjectScanner 格式完全一致的 (export_table, call_graph, import_graph)
    """
    export_table = {}

    for rel_path, source in repo_files.items():
        if not rel_path.endswith(".py") or rel_path.endswith("__init__.py"):
            continue

        result = {
            "classes": [], "functions": [],
            "imports": [], "exports": [], "calls": []
        }
        try:
            tree = ast.parse(source)

            result["classes"] = [
                node.name for node in tree.body
                if isinstance(node, ast.ClassDef)
            ]
            result["functions"] = [
                node.name for node in tree.body
                if isinstance(node, ast.FunctionDef)
            ]

            # 类方法
            class_methods = []
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if not (item.name.startswith("__") and item.name.endswith("__")):
                                class_methods.append(item.name)

            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({"type": "import", "module": alias.name, "symbol": None})
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append({"type": "from", "module": module, "symbol": alias.name})
            result["imports"] = imports

            calls = []
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                if func_name:
                    calls.append(func_name)
            result["calls"] = list(set(calls))

            exports = list(set(
                result["functions"] + result["classes"] + class_methods
            ))
            result["exports"] = exports
            export_table[rel_path] = result

        except Exception:
            continue

    # import_graph
    import_graph = {}
    for file_path, info in export_table.items():
        import_graph[file_path] = list(set(
            imp["module"] for imp in info["imports"] if imp["module"]
        ))

    # call_graph
    call_graph = {}
    all_exports = {}
    for file_path, info in export_table.items():
        for symbol in info["exports"]:
            all_exports[symbol] = file_path

    for file_path, info in export_table.items():
        called_files = list(set(
            all_exports[call_name]
            for call_name in info["calls"]
            if call_name in all_exports and all_exports[call_name] != file_path
        ))
        call_graph[file_path] = called_files

    return export_table, call_graph, import_graph


if __name__ == "__main__":
    scanner = ProjectScanner(repo_root="./tests/benchmark_project_v1")
    result = scanner.scan()
    print(result["tree"])

    print("\n===== EXPORT TABLE =====\n")
    from pprint import pprint
    pprint(scanner.get_export_table())

    print("\n===== IMPORT GRAPH =====\n")
    pprint(scanner.get_import_graph())

    print("\n===== CALL GRAPH =====\n")
    pprint(scanner.get_call_graph())