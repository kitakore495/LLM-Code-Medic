from pydantic import BaseModel


class RepairRequest(BaseModel):

    repo_root: str

    error_message: str


class DiagnoseRequest(BaseModel):

    repo_root: str

    error_message: str