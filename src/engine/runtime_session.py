import os

from langchain_openai import ChatOpenAI


class RuntimeSession:

    def __init__(self):

        self.diagnose_provider = os.getenv(
            "DIAGNOSE_PROVIDER",
            "deepseek"
        ).lower()

        self.diagnose_model = os.getenv(
            "DIAGNOSE_MODEL"
        )

        self.repair_provider = os.getenv(
            "REPAIR_PROVIDER",
            "deepseek"
        ).lower()

        self.repair_model = os.getenv(
            "REPAIR_MODEL"
        )

    # =========================================================
    # Provider -> LLM Factory
    # =========================================================
    def _build_llm(
        self,
        provider: str,
        model_name: str,
        temperature: float = 0.2
    ):

        if provider == "deepseek":

            api_key = os.getenv(
                "DEEPSEEK_API_KEY"
            )

            api_base = os.getenv(
                "DEEPSEEK_API_BASE"
            )

            if not api_key:
                raise RuntimeError(
                    "缺少 DEEPSEEK_API_KEY"
                )

            if not api_base:
                raise RuntimeError(
                    "缺少 DEEPSEEK_API_BASE"
                )

            return ChatOpenAI(
                model=model_name,
                api_key=api_key,
                base_url=api_base,
                temperature=temperature
            )

        elif provider == "gemini":

            api_key = os.getenv(
                "GEMINI_API_KEY"
            )

            if not api_key:
                raise RuntimeError(
                    "缺少 GEMINI_API_KEY"
                )

            return ChatOpenAI(
                model=model_name,
                api_key=api_key,
                base_url=(
                    "https://generativelanguage.googleapis.com/v1beta/openai/"
                ),
                temperature=temperature
            )

        raise RuntimeError(
            f"未知 Provider: {provider}"
        )

    # =========================================================
    # Diagnose Model
    # =========================================================
    def get_diagnose_llm(self):

        return self._build_llm(
            provider=self.diagnose_provider,
            model_name=self.diagnose_model,
            temperature=0.2
        )

    # =========================================================
    # Repair Model
    # =========================================================
    def get_repair_llm(self):

        return self._build_llm(
            provider=self.repair_provider,
            model_name=self.repair_model,
            temperature=0.2
        )