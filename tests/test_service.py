import os
import sys

from dotenv import load_dotenv

# =========================================================
# 项目根目录
# =========================================================

ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# =========================================================
# 加入 PYTHONPATH
# =========================================================

if ROOT_DIR not in sys.path:
    sys.path.insert(
        0,
        ROOT_DIR
    )

# =========================================================
# 加载 .env
# 必须在导入 runtime_config 之前
# =========================================================

ENV_PATH = os.path.join(
    ROOT_DIR,
    ".env"
)

load_dotenv(
    dotenv_path=ENV_PATH,
    override=True
)

# =========================================================
# 导入项目模块
# =========================================================

from src.config.runtime_config import (
    runtime_config
)

from src.service.medic_service import (
    MedicService
)

# =========================================================
# 调试信息
# =========================================================

print("\n==============================")
print("Runtime Config Check")
print("==============================")

print(
    "DEEPSEEK_API_KEY =",
    runtime_config.deepseek_api_key
)

print(
    "GEMINI_API_KEY =",
    runtime_config.gemini_api_key
)

print(
    "DIAGNOSE_PROVIDER =",
    runtime_config.diagnose_provider
)

print(
    "REPAIR_PROVIDER =",
    runtime_config.repair_provider
)

print("==============================\n")

# =========================================================
# 测试错误
# =========================================================

ERROR = """
Traceback (most recent call last):
  File "main.py", line 11, in run_pipeline
    result = utils.compute_core_logic(input_data)
AttributeError: module 'utils' has no attribute 'compute_core_logic'
"""

# =========================================================
# Service 测试
# =========================================================

service = MedicService()

result = service.repair(
    repo_root=runtime_config.test_repo_root,
    error_message=ERROR
)

print("\n==============================")
print("Service Result")
print("==============================")

print(
    "success =",
    result.get("success")
)

print(
    "is_fixed =",
    result.get("is_fixed")
)

print(
    "repairable =",
    result.get("repairable")
)

print(
    "root_cause =",
    result.get("root_cause")
)

print(
    "modified_files =",
    result.get("modified_files")
)

print("==============================")