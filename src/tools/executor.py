import subprocess
import sys
import os
import tempfile

class CodeExecutor:
    def __init__(self, timeout=10):
        self.timeout = timeout

    def run_code(self, code_content: str, repo_root: str = None):
        """
        运行代码并返回结果。
        repo_root: 如果传入了仓库根目录，临时文件将创建在仓库内，以确保能正确 import 同级模块。
        """
        # ✨ V2 核心修正：如果指定了仓库，就在仓库目录下创建临时文件，否则使用系统默认
        dir_to_use = repo_root if (repo_root and os.path.exists(repo_root)) else None
        temp_file_path = None

        try:
            # ✨ 将 with 块独立，保证文件写入完成并安全关闭后，再进行 subprocess 调用与销毁
            with tempfile.NamedTemporaryFile(
                suffix=".py", 
                delete=False, 
                mode='w', 
                encoding='utf-8',
                dir=dir_to_use  # ✨ 强制让临时文件和 utils.py 待在同一个物理文件夹里
            ) as f:
                temp_file_path = f.name
                f.write(code_content)
        
            # ✨ V2 核心修正：不仅要在对应目录下运行，还要把工作目录 (cwd) 切换过去
            result = subprocess.run(
                [sys.executable, temp_file_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=dir_to_use  # ✨ 确保 Python 解释器运行时的相对路径正确
            )
            
            if result.returncode == 0:
                return {"success": True, "output": result.stdout, "error": None}
            else:
                return {"success": False, "output": result.stdout, "error": result.stderr}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": f"Error: Execution timed out after {self.timeout} seconds."}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
        finally:
            # ✨ 此时文件句柄已安全释放，在 Windows 下绝对不会触发无权访问的 PermissionError 
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)