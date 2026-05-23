import os
import sys
from dotenv import load_dotenv

# =========================================================
# 全局环境变量必须最先加载
# =========================================================
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

ENV_PATH = os.path.join(
    ROOT_DIR,
    ".env"
)

load_dotenv(
    dotenv_path=ENV_PATH,
    override=True
)

# 加入 PYTHONPATH
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.engine.medic_engine import MedicEngine


def main():

    engine = MedicEngine()

    engine.run()


if __name__ == "__main__":
    main()