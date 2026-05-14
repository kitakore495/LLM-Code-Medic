import subprocess
import sys
import os
import tempfile
import traceback

class CodeExecutor:
    def __init__(self, timeout=10):
        self.timeout = timeout

    def run_code(self, code_content: str):
        """
        创建一个临时文件运行代码，并返回执行结果。
        """
        # 使用 tempfile 创建临时文件，避免污染项目目录
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w', encoding='utf-8') as f:
            temp_file_path = f.name
            f.write(code_content)
        
        try:
            # 执行代码
            result = subprocess.run(
                [sys.executable, temp_file_path],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout,
                    "error": None
                }
            else:
                # 捕获标准错误流（Runtime Error / Syntax Error 等）
                return {
                    "success": False,
                    "output": result.stdout,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Error: Execution timed out after {self.timeout} seconds."
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
        finally:
            # 跑完一定要把临时文件删掉，保持整洁
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
