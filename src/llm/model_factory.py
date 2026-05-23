import os

from langchain_openai import ChatOpenAI


def create_model(
    provider: str,
    model_name: str,
    temperature: float = 0.2
):
    """
    创建大模型实例

    provider:
        - deepseek
        - gemini
    """

    provider = provider.lower().strip()

    # =========================================================
    # DeepSeek
    # =========================================================
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
            temperature=temperature,
            api_key=api_key,
            base_url=api_base
        )

    # =========================================================
    # Gemini（懒加载避免强依赖）
    # =========================================================
    elif provider == "gemini":

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:
            raise RuntimeError(
                "缺少 GEMINI_API_KEY"
            )

        try:
            from langchain_google_genai import (
                ChatGoogleGenerativeAI
            )

        except ImportError:
            raise RuntimeError(
                "未安装 langchain-google-genai，请执行："
                "\npip install langchain-google-genai"
            )

        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature
        )

    # =========================================================
    # Unsupported Provider
    # =========================================================
    raise RuntimeError(
        f"不支持的 Provider: {provider}"
    )