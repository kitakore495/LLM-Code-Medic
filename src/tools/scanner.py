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

    def _get_py_info(self, file_path):

        try:
            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:
                node = ast.parse(f.read())

            classes = [
                n.name
                for n in node.body
                if isinstance(n, ast.ClassDef)
            ]

            functions = [
                n.name
                for n in node.body
                if isinstance(n, ast.FunctionDef)
            ]

            info = []

            if classes:
                info.append(
                    f"classes: {', '.join(classes)}"
                )

            if functions:
                info.append(
                    f"defs: {', '.join(functions)}"
                )

            return (
                f" ({' | '.join(info)})"
                if info
                else ""
            )

        except Exception:
            return " (parse error)"

    def scan(self):

        tree = []

        for root, dirs, files in os.walk(self.repo_root):

            dirs[:] = [
                d for d in dirs
                if d not in self.ignore_list
            ]

            level = root.replace(
                self.repo_root,
                ""
            ).count(os.sep)

            indent = " " * 4 * level

            folder_name = (
                os.path.basename(root)
                or self.repo_root
            )

            tree.append(
                f"{indent}📂 {folder_name}/"
            )

            sub_indent = " " * 4 * (level + 1)

            for f in files:

                if (
                    f.endswith(".py")
                    and f != "__init__.py"
                ):

                    full_path = os.path.join(root, f)

                    py_info = self._get_py_info(
                        full_path
                    )

                    tree.append(
                        f"{sub_indent}📄 {f}{py_info}"
                    )

        return "\n".join(tree)


if __name__ == "__main__":
    scanner = ProjectScanner()

    print(scanner.scan())