from langchain_openai import (
    ChatOpenAI
)

from src.config.runtime_config import (
    runtime_config
)


class ModelFactory:

    # =========================================================
    # Create LLM
    # =========================================================
    @staticmethod
    def create_llm(
        provider: str,
        model_name: str,
        temperature: float = 0.2
    ):

        provider = (
            provider
            .lower()
            .strip()
        )

        timeout = (
            runtime_config
            .llm_timeout
        )

        # =====================================================
        # DeepSeek
        # (SiliconFlow OpenAI Compatible)
        # =====================================================
        if provider == "deepseek":

            api_key = (
                runtime_config
                .deepseek_api_key
            )

            api_base = (
                runtime_config
                .deepseek_api_base
            )

            if not api_key:

                raise RuntimeError(
                    "缺少 "
                    "DEEPSEEK_API_KEY"
                )

            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=api_key,
                base_url=api_base,
                timeout=timeout,
                max_retries=0
            )

        # =====================================================
        # Gemini
        # 延迟导入避免依赖崩溃
        # =====================================================
        elif provider == "gemini":

            api_key = (
                runtime_config
                .gemini_api_key
            )

            if not api_key:

                raise RuntimeError(
                    "缺少 "
                    "GEMINI_API_KEY"
                )

            try:

                from langchain_google_genai import (
                    ChatGoogleGenerativeAI
                )

            except ImportError:

                raise RuntimeError(
                    "\n检测到 provider=gemini，"
                    "\n但未安装依赖："
                    "\n\npip install "
                    "langchain-google-genai"
                )

            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=temperature,
                timeout=timeout
            )

        # =====================================================
        # Unsupported
        # =====================================================
        raise RuntimeError(
            f"未知 provider: "
            f"{provider}"
        )