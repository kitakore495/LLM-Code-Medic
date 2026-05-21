import os
import sys
import shutil
import subprocess
import traceback
from typing import Dict, Tuple

class CodeExecutor:
    """
    V3 工业级沙箱执行器：支持多文件同时物理装配、运行期环境隔离以及失败一键原子回滚。
    """
    def __init__(self, repo_root: str):
        """
        初始化执行器
        :param repo_root: 测试仓库的绝对物理根目录 (例如: "C:/.../LLM-Code-Medic/tests/v2_repo_case")
        """
        self.repo_root = os.path.abspath(repo_root)

    def run_v3_validation(self, repo_files: Dict[str, str]) -> Tuple[bool, str]:
        """
        【V3 核心方法】全量多文件联合编译与物理回滚验证
        :param repo_files: 包含整个仓库最新代码映射的字典 {"相对路径": "全量代码"}
        :return: (是否运行成功, 错误信息/Traceback)
        """
        print(f"   [Sandbox] 开始为整个测试仓库进行多文件全物理装配...")
        
        # 1. 内存全量备份：在物理改写磁盘前，先对当前磁盘上的原文件做快照备份，用于失败回滚
        backup_files: Dict[str, str] = {}
        
        try:
            # 2. 物理写入：将大模型生成的最新多文件代码字典，覆盖写入到对应的磁盘物理路径中
            for relative_path, code_content in repo_files.items():
                # 拼接成绝对路径
                full_path = os.path.abspath(os.path.join(self.repo_root, relative_path))
                
                # 安全防御：严防大模型利用路径穿越漏洞（如 ../../ ）攻击本地系统
                if not full_path.startswith(self.repo_root):
                    print(f"   ⚠️ [Security Warning] 检测到非法的路径穿越尝试: {relative_path}，已拒绝写入。")
                    continue
                
                # 如果原文件在磁盘上存在，读取原内容进备份区，用于原子回滚
                if os.path.exists(full_path):
                    with open(full_path, "r", encoding="utf-8") as f:
                        backup_files[relative_path] = f.read()
                else:
                    # 如果是一个原本不存在的新增文件，备份区标记为 None，回滚时直接物理删除
                    backup_files[relative_path] = None
                
                # 确保上级物理目录存在，如果不存在（大模型新建了子文件夹）则自动创建
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # 将大模型打好补丁的代码全量写入磁盘
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(code_content)
                    
            print(f"   [Sandbox] 多文件装配完毕，共打入 {len(repo_files)} 个文件的联动补丁。")
            
            # 3. 物理隔离测试：拉起独立子进程，在测试仓库的工作目录（CWD）下运行主入口
            # 默认运行测试仓库下的 main.py。组长如果想改测试入口，直接在这里调配
            test_entry = os.path.join(self.repo_root, "main.py")
            
            if not os.path.exists(test_entry):
                raise FileNotFoundError(f"在测试仓库中未找到主入口文件: {test_entry}")
                
            print(f"   [Sandbox] 正在拉起沙箱进程，运行: python main.py ...")
            
            # 关键技术：使用 subprocess.run 并强行指定 cwd=self.repo_root 物理切分运行上下文
            # 这样 Python 解释器在加载同级模块时，会天然以当前测试仓库为基准，免疫 ModuleNotFoundError
            result = subprocess.run(
                [sys.executable, "main.py"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=15  # 15秒超时防御，防止大模型写出死循环导致系统卡死
            )
            
            # 4. 判定运行结果与捕获 Traceback
            if result.returncode == 0:
                # 运行成功，打印输出（用于调试观摩）
                if result.stdout:
                    print(f"\n--- 沙箱标准输出 (STDOUT) ---\n{result.stdout.strip()}\n-----------------------------")
                return True, ""
            else:
                # 联合测试挂了，提取标准错误输出
                error_log = result.stderr if result.stderr else result.stdout
                print(f"   [Sandbox Error] 联合测试运行失败！退出码: {result.returncode}")
                
                # 5. 【原子回滚】一旦失败，立刻触发物理复原逻辑，消除脏代码污染
                self._rollback(backup_files)
                return False, error_log.strip()
                
        except subprocess.TimeoutExpired:
            print("   🚨 [Sandbox Timeout] 沙箱测试超时！疑似代码中包含死循环。强制熔断并执行回滚。")
            self._rollback(backup_files)
            return False, "RuntimeError: Execution timed out (Possible Infinite Loop detected in patched code)."
            
        except Exception as e:
            # 捕获执行器自身的潜在异常，也必须安全回滚
            print(f"   ⚠️ [Sandbox Exception] 执行器内部触发异常: {e}")
            self._rollback(backup_files)
            return False, traceback.format_exc()

    def _rollback(self, backup_files: Dict[str, str]):
        """
        内部一键物理回滚机制：将磁盘上的文件完美复原到修改前的状态
        """
        print("   🧹 [Rollback] 正在启动多文件物理原子回滚...")
        for relative_path, original_content in backup_files.items():
            full_path = os.path.abspath(os.path.join(self.repo_root, relative_path))
            try:
                if original_content is None:
                    # 如果原先文件不存在，属于大模型瞎编的，直接物理删除
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        print(f"      -> 已物理清理新增的临时文件: {relative_path}")
                else:
                    # 如果原先有这个文件，将备份的内容重新写回，洗掉大模型的脏代码
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(original_content)
                    print(f"      -> 已成功恢复原文件快照: {relative_path}")
            except Exception as rollback_err:
                print(f"      ❌ 恢复文件 {relative_path} 失败: {rollback_err}")
        print("   🧹 [Rollback] 本地物理测试环境已全部干净复原。")