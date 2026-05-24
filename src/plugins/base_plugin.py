from abc import (
    ABC,
    abstractmethod
)

from typing import Dict


class BasePlugin(
    ABC
):

    name = "base"

    @abstractmethod
    def run(
        self,
        repo_files: Dict[str, str],
        analysis: str
    ) -> Dict[str, str]:
        """
        插件统一入口

        Parameters
        ----------
        repo_files:
            当前仓库文件快照

        analysis:
            Diagnose 阶段输出的根因分析

        Returns
        -------
        Dict[str, str]

        返回修改后的 repo_files
        """
        pass