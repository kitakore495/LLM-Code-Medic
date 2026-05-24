from src.config.runtime_config import (
    runtime_config
)


class ProviderRouter:

    # =========================================================
    # Diagnose Provider
    # =========================================================
    @staticmethod
    def get_diagnose_provider():

        provider = (
            runtime_config
            .diagnose_provider
            .lower()
            .strip()
        )

        supported = [
            "deepseek",
            "gemini"
        ]

        if provider not in supported:

            raise ValueError(
                "不支持的 Diagnose Provider: "
                f"{provider}"
            )

        return provider

    # =========================================================
    # Diagnose Model
    # =========================================================
    @staticmethod
    def get_diagnose_model():

        model = (
            runtime_config
            .diagnose_model
            .strip()
        )

        if not model:

            raise RuntimeError(
                "DIAGNOSE_MODEL 未配置"
            )

        return model

    # =========================================================
    # Repair Provider
    # =========================================================
    @staticmethod
    def get_repair_provider():

        provider = (
            runtime_config
            .repair_provider
            .lower()
            .strip()
        )

        supported = [
            "deepseek",
            "gemini"
        ]

        if provider not in supported:

            raise ValueError(
                "不支持的 Repair Provider: "
                f"{provider}"
            )

        return provider

    # =========================================================
    # Repair Model
    # =========================================================
    @staticmethod
    def get_repair_model():

        model = (
            runtime_config
            .repair_model
            .strip()
        )

        if not model:

            raise RuntimeError(
                "REPAIR_MODEL 未配置"
            )

        return model

    # =========================================================
    # Debug
    # =========================================================
    @staticmethod
    def is_debug():

        return runtime_config.debug

    # =========================================================
    # Runtime Config Print
    # =========================================================
    @staticmethod
    def print_runtime_config():

        print(
            "\n🧠 当前运行配置"
        )

        print(
            f"   Diagnose: "
            f"{runtime_config.diagnose_provider}"
            f" | "
            f"{runtime_config.diagnose_model}"
        )

        print(
            f"   Repair: "
            f"{runtime_config.repair_provider}"
            f" | "
            f"{runtime_config.repair_model}"
        )

        print(
            f"   Debug: "
            f"{runtime_config.debug}"
        )