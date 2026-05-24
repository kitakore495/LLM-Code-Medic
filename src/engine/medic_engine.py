from src.engine.repair_pipeline import (
    RepairPipeline
)


class MedicEngine:

    def __init__(
        self,
        repo_root: str
    ):

        self.repo_root = (
            repo_root
        )

        self.pipeline = (
            RepairPipeline(
                repo_root=repo_root
            )
        )

    def run(
        self
    ):

        self.pipeline.execute()