from fastapi import APIRouter

from src.service.medic_service import (
    MedicService
)

from server.schemas.request import (
    RepairRequest
)

router = APIRouter()

service = MedicService()


@router.post("/repair")
async def repair(
    request: RepairRequest
):

    return service.repair(
        repo_root=request.repo_root,
        error_message=request.error_message
    )