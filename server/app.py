import os
import sys

from dotenv import load_dotenv

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

if ROOT_DIR not in sys.path:
    sys.path.insert(
        0,
        ROOT_DIR
    )

from fastapi import FastAPI

from server.routes.repair import (
    router as repair_router
)

from server.routes.diagnose import (
    router as diagnose_router
)

from server.routes.health import (
    router as health_router
)

app = FastAPI(
    title="LLM Code Medic API",
    version="1.0.0"
)

app.include_router(
    health_router
)

app.include_router(
    diagnose_router
)

app.include_router(
    repair_router
)