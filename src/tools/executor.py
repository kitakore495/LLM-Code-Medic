import os
import sys
import shutil
import subprocess
import traceback

from typing import Dict, Tuple


class CodeExecutor:

    def __init__(self, repo_root: str):

        # tests/v3
        self.repo_root = os.path.abspath(repo_root)

        # 项目根目录
        self.project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )
        )

        # output/
        self.output_root = os.path.join(
            self.project_root,
            "output"
        )

    # =========================================================
    # 安全路径拼接
    # =========================================================
    def _safe_join(
        self,
        root: str,
        relative_path: str
    ):

        full_path = os.path.abspath(
            os.path.join(root, relative_path)
        )

        root_real = os.path.realpath(root)
        full_real = os.path.realpath(full_path)

        if os.path.commonpath([
            root_real,
            full_real
        ]) != root_real:

            raise ValueError(
                f"非法路径穿越: {relative_path}"
            )

        return full_path

    # =========================================================
    # 创建 output 工作区
    # =========================================================
    def _prepare_output_workspace(self):

        # 删除旧 output
        if os.path.exists(self.output_root):
            shutil.rmtree(self.output_root)

        # 复制 tests/v3 -> output
        shutil.copytree(
            self.repo_root,
            self.output_root,
            ignore=shutil.ignore_patterns(
                "__pycache__",
                "*.pyc"
            )
        )

        print(
            f"   📦 已创建影子工作区: "
            f"{self.output_root}"
        )

    # =========================================================
    # 清理 pycache
    # =========================================================
    def _clean_pycache(self):

        for root, dirs, files in os.walk(
            self.output_root
        ):

            for d in dirs:

                if d == "__pycache__":

                    shutil.rmtree(
                        os.path.join(root, d),
                        ignore_errors=True
                    )

            for f in files:

                if f.endswith(".pyc"):

                    try:
                        os.remove(
                            os.path.join(root, f)
                        )
                    except:
                        pass

    # =========================================================
    # 写入修复文件
    # =========================================================
    def _write_output_files(
        self,
        repo_files: Dict[str, str]
    ):

        print(
            "   [Sandbox] 正在写入修复后的文件..."
        )

        for relative_path, code_content in repo_files.items():

            full_path = self._safe_join(
                self.output_root,
                relative_path
            )

            os.makedirs(
                os.path.dirname(full_path),
                exist_ok=True
            )

            with open(
                full_path,
                "w",
                encoding="utf-8"
            ) as f:
                f.write(code_content)

            print(
                f"      -> 已输出: "
                f"{relative_path}"
            )

        print(
            f"   ✅ 已完成 "
            f"{len(repo_files)} 个文件输出"
        )

    # =========================================================
    # 执行 output/main.py
    # =========================================================
    def _run_output_sandbox(self):

        self._clean_pycache()

        test_entry = os.path.join(
            self.output_root,
            "main.py"
        )

        if not os.path.exists(test_entry):

            raise FileNotFoundError(
                f"output 中缺少 main.py"
            )

        print(
            f"   📌 Sandbox CWD: "
            f"{self.output_root}"
        )

        print(
            f"   📌 Sandbox Entry: "
            f"{test_entry}"
        )

        print(
            "   🚀 正在 output/ 沙箱中运行..."
        )

        sandbox_env = os.environ.copy()

        # 禁止 pycache
        sandbox_env[
            "PYTHONDONTWRITEBYTECODE"
        ] = "1"

        # 强制 UTF-8
        sandbox_env[
            "PYTHONIOENCODING"
        ] = "utf-8"

        # output 优先级最高
        sandbox_env[
            "PYTHONPATH"
        ] = self.output_root

        result = subprocess.run(
            [sys.executable, "main.py"],
            cwd=self.output_root,
            capture_output=True,
            text=True,
            timeout=15,
            env=sandbox_env,
            encoding="utf-8",
            errors="replace"
        )

        print(
            "\n================ STDOUT ================"
        )

        print(result.stdout)

        print(
            "\n================ STDERR ================"
        )

        print(result.stderr)

        print(
            "========================================"
        )

        return result

    # =========================================================
    # 主验证入口
    # =========================================================
    def run_v3_validation(
        self,
        repo_files: Dict[str, str]
    ) -> Tuple[bool, str]:

        try:

            print(
                "   [Sandbox] 正在创建 Output 工作区..."
            )

            # 1. 创建 output
            self._prepare_output_workspace()

            # 2. 写入修复文件
            self._write_output_files(
                repo_files
            )

            # 3. 运行沙箱
            result = self._run_output_sandbox()

            # 4. 判定结果
            if result.returncode == 0:

                print(
                    "\n🎉 Output 工作区测试通过"
                )

                return True, ""

            error_log = (
                result.stderr
                if result.stderr
                else result.stdout
            )

            print(
                "\n❌ Output 工作区测试失败"
            )

            return False, error_log

        except subprocess.TimeoutExpired:

            print(
                "\n🚨 沙箱运行超时"
            )

            return (
                False,
                "Execution timed out"
            )

        except Exception:

            print(
                "\n🚨 执行器内部异常"
            )

            return (
                False,
                traceback.format_exc()
            )