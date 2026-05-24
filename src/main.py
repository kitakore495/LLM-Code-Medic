import os
import sys

from dotenv import (
    load_dotenv
)

# =========================================================
# 全局环境变量最先加载
# =========================================================
ROOT_DIR = (
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(
                __file__
            )
        )
    )
)

ENV_PATH = (
    os.path.join(
        ROOT_DIR,
        ".env"
    )
)

load_dotenv(
    dotenv_path=ENV_PATH,
    override=True
)

# =========================================================
# PYTHONPATH
# =========================================================
if ROOT_DIR not in sys.path:

    sys.path.insert(
        0,
        ROOT_DIR
    )

from src.engine.medic_engine import (
    MedicEngine
)

from src.config.runtime_config import (
    runtime_config
)


def main():

    print(
        "=" * 50
    )

    print(
        "🎬 启动 "
        "LLM-Code-Medic V4 "
        "多文件智能协同修复系统..."
    )

    print(
        f"📂 当前目标测试仓库: "
        f"{runtime_config.test_repo_root}"
    )

    print(
        "=" * 50
    )

    if not os.path.exists(
        runtime_config.test_repo_root
    ):

        print(
            "❌ 错误: "
            "未找到测试仓库路径 "
            f"{runtime_config.test_repo_root}"
        )

        return

    engine = MedicEngine(
        repo_root=(
            runtime_config
            .test_repo_root
        )
    )

    engine.run()


if __name__ == "__main__":
    main()