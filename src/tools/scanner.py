# src/tools/scanner.py
import os
import ast

class ProjectScanner:
    def __init__(self, repo_root="."):  # 👈 【修复】将 root_path 统一对齐为 repo_root
        self.repo_root = os.path.abspath(repo_root)
        self.ignore_list = {
            ".git", "__pycache__", ".venv", "venv", 
            "output", ".env", ".vscode", ".pytest_cache" 
        }

    def _get_py_info(self, file_path):
        """
        使用 AST (抽象语法树) 提取 Python 文件中的类名和函数名
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                node = ast.parse(f.read())
            
            classes = [n.name for n in node.body if isinstance(n, ast.ClassDef)]
            functions = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            
            info = []
            if classes: info.append(f"classes: {', '.join(classes)}")
            if functions: info.append(f"defs: {', '.join(functions)}")
            return f" ({' | '.join(info)})" if info else ""
        except Exception:
            return " (parse error)"

    def scan(self) -> str:  # 👈 【修复】将方法名从 scan_structure 改为 scan，完美对齐 main.py
        """生成增强版的项目目录树结构"""
        tree = []
        for root, dirs, files in os.walk(self.repo_root):
            # 过滤忽略目录
            dirs[:] = [d for d in dirs if d not in self.ignore_list]
            
            # 计算缩进层级
            level = root.replace(self.repo_root, '').count(os.sep)
            indent = ' ' * 4 * level
            
            # 添加文件夹名
            folder_name = os.path.basename(root) or self.repo_root
            tree.append(f"{indent}📂 {folder_name}/")
            
            # 添加该目录下的 Python 文件及其元数据
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                if f.endswith(".py") and f != "__init__.py":
                    full_path = os.path.join(root, f)
                    py_info = self._get_py_info(full_path)
                    tree.append(f"{sub_indent}📄 {f}{py_info}")
                    
        return "\n".join(tree)

if __name__ == "__main__":
    # 组长可以在本地直接运行此文件进行效果预览
    scanner = ProjectScanner()
    print("--- [V3] 仓库级全景扫描地图 ---")
    print(scanner.scan())