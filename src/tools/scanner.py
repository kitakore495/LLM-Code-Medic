import os
import ast


class ProjectScanner:

    def __init__(self, repo_root="."):

        self.repo_root = os.path.abspath(repo_root)

        self.ignore_list = {
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            ".pytest_cache",
            ".vscode"
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

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:

                source = f.read()

            tree = ast.parse(source)

            # ==================================
            # Classes
            # ==================================
            result["classes"] = [
                node.name
                for node in tree.body
                if isinstance(
                    node,
                    ast.ClassDef
                )
            ]

            # ==================================
            # Functions
            # ==================================
            result["functions"] = [
                node.name
                for node in tree.body
                if isinstance(
                    node,
                    ast.FunctionDef
                )
            ]

            # ==================================
            # Imports
            # ==================================
            imports = []

            for node in ast.walk(tree):

                if isinstance(
                    node,
                    ast.Import
                ):

                    for alias in node.names:

                        imports.append({
                            "type": "import",
                            "module": alias.name,
                            "symbol": None
                        })

                elif isinstance(
                    node,
                    ast.ImportFrom
                ):

                    module = (
                        node.module
                        or ""
                    )

                    for alias in node.names:

                        imports.append({
                            "type": "from",
                            "module": module,
                            "symbol": alias.name
                        })

            result["imports"] = imports

            # ==================================
            # Calls
            # ==================================
            calls = []

            for node in ast.walk(tree):

                if not isinstance(
                    node,
                    ast.Call
                ):
                    continue

                func_name = None

                if isinstance(
                    node.func,
                    ast.Name
                ):

                    func_name = (
                        node.func.id
                    )

                elif isinstance(
                    node.func,
                    ast.Attribute
                ):

                    func_name = (
                        node.func.attr
                    )

                if func_name:

                    calls.append(
                        func_name
                    )

            result["calls"] = list(
                set(calls)
            )

            # ==================================
            # Exports
            # ==================================
            exports = []

            exports.extend(
                result["classes"]
            )

            exports.extend(
                result["functions"]
            )

            result["exports"] = exports

            return result

        except Exception:

            return None

    def _build_file_info(
        self,
        parsed_info
    ):

        if not parsed_info:
            return " (parse error)"

        info = []

        if parsed_info["classes"]:

            info.append(
                "classes: "
                + ", ".join(
                    parsed_info["classes"]
                )
            )

        if parsed_info["functions"]:

            info.append(
                "defs: "
                + ", ".join(
                    parsed_info["functions"]
                )
            )

        if parsed_info["imports"]:

            info.append(
                f"imports: {len(parsed_info['imports'])}"
            )

        if parsed_info["calls"]:

            info.append(
                f"calls: {len(parsed_info['calls'])}"
            )

        return (
            f" ({' | '.join(info)})"
            if info
            else ""
        )

    def _build_import_graph(self):

        graph = {}

        for file_path, info in self.export_table.items():

            imports = []

            for imp in info["imports"]:

                module = imp["module"]

                if module:

                    imports.append(
                        module
                    )

            graph[file_path] = list(
                set(imports)
            )

        self.import_graph = graph

    def _build_call_graph(self):

        graph = {}

        all_exports = {}

        for file_path, info in self.export_table.items():

            for symbol in info["exports"]:

                all_exports[
                    symbol
                ] = file_path

        for file_path, info in self.export_table.items():

            called_files = []

            for call_name in info["calls"]:

                if (
                    call_name
                    in all_exports
                ):

                    target_file = (
                        all_exports[
                            call_name
                        ]
                    )

                    if (
                        target_file
                        != file_path
                    ):

                        called_files.append(
                            target_file
                        )

            graph[file_path] = list(
                set(called_files)
            )

        self.call_graph = graph

    def scan(self):

        self.export_table = {}
        self.import_graph = {}
        self.call_graph = {}

        tree = []

        for root, dirs, files in os.walk(
            self.repo_root
        ):

            dirs[:] = [
                d
                for d in dirs
                if d not in self.ignore_list
            ]

            level = root.replace(
                self.repo_root,
                ""
            ).count(os.sep)

            indent = (
                " " * 4 * level
            )

            folder_name = (
                os.path.basename(root)
                or self.repo_root
            )

            tree.append(
                f"{indent}📂 {folder_name}/"
            )

            sub_indent = (
                " " * 4 * (level + 1)
            )

            for file_name in files:

                if (
                    not file_name.endswith(".py")
                    or file_name == "__init__.py"
                ):
                    continue

                full_path = os.path.join(
                    root,
                    file_name
                )

                rel_path = os.path.relpath(
                    full_path,
                    self.repo_root
                ).replace(
                    "\\",
                    "/"
                )

                parsed_info = (
                    self._parse_python_file(
                        full_path
                    )
                )

                if parsed_info:

                    self.export_table[
                        rel_path
                    ] = parsed_info

                tree.append(
                    f"{sub_indent}📄 "
                    f"{file_name}"
                    f"{self._build_file_info(parsed_info)}"
                )

        self._build_import_graph()
        self._build_call_graph()

        return {
            "tree":
                "\n".join(tree),

            "export_table":
                self.export_table,

            "call_graph":
                self.call_graph,

            "import_graph":
                self.import_graph,
        }

    def scan_project(self):

        return self.scan()

    def get_export_table(self):

        return self.export_table

    def get_call_graph(self):

        return self.call_graph

    def get_import_graph(self):

        return self.import_graph


if __name__ == "__main__":

    scanner = ProjectScanner()

    result = scanner.scan()

    print(result["tree"])

    print("\n===== EXPORT TABLE =====\n")

    from pprint import pprint

    pprint(
        scanner.get_export_table()
    )

    print("\n===== IMPORT GRAPH =====\n")

    pprint(
        scanner.get_import_graph()
    )

    print("\n===== CALL GRAPH =====\n")

    pprint(
        scanner.get_call_graph()
    )