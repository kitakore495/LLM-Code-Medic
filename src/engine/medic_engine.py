from src.engine.repair_pipeline import (
    RepairPipeline
)

from src.engine.runtime_session import (
    RuntimeSession
)


class MedicEngine:

    def __init__(self):

        self.session = RuntimeSession()

        self.pipeline = RepairPipeline()

    def run(self):

        self.pipeline.execute()