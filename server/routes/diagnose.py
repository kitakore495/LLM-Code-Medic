from fastapi import APIRouter

from src.service.medic_service import (
    MedicService
)

from server.schemas.request import (
    DiagnoseRequest
)

router = APIRouter()

service = MedicService()


@router.post("/diagnose")
async def diagnose(
    request: DiagnoseRequest
):

    return service.diagnose(
        repo_root=request.repo_root,
        error_message=request.error_message
    )