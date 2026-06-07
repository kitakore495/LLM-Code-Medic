import os

from dataclasses import (
    dataclass
)


@dataclass
class RuntimeConfig:

    # =========================================================
    # Diagnose
    # =========================================================
    diagnose_provider: str
    diagnose_model: str

    # =========================================================
    # Repair
    # =========================================================
    repair_provider: str
    repair_model: str

    # =========================================================
    # Fallback
    # =========================================================
    fallback_provider: str
    fallback_model: str

    # =========================================================
    # API
    # =========================================================
    deepseek_api_key: str
    deepseek_api_base: str

    gemini_api_key: str

    # =========================================================
    # Runtime
    # =========================================================
    debug: bool

    # =========================================================
    # Repo
    # =========================================================
    test_repo_root: str

    # =========================================================
    # LLM Resilience
    # =========================================================
    llm_retry_count: int
    llm_timeout: int
    llm_backoff_seconds: int


def _to_bool(
    value: str
) -> bool:

    return str(
        value
    ).lower() in [
        "1",
        "true",
        "yes",
        "on"
    ]


runtime_config = RuntimeConfig(

    # =====================================================
    # Diagnose
    # =====================================================
    diagnose_provider=os.getenv(
        "DIAGNOSE_PROVIDER",
        "deepseek"
    ),

    diagnose_model=os.getenv(
        "DIAGNOSE_MODEL",
        "deepseek-ai/DeepSeek-V3"
    ),

    # =====================================================
    # Repair
    # =====================================================
    repair_provider=os.getenv(
        "REPAIR_PROVIDER",
        "deepseek"
    ),

    repair_model=os.getenv(
        "REPAIR_MODEL",
        "deepseek-ai/DeepSeek-V3"
    ),

    # =====================================================
    # Fallback
    # =====================================================
    fallback_provider=os.getenv(
        "FALLBACK_PROVIDER",
        "gemini"
    ),

    fallback_model=os.getenv(
        "FALLBACK_MODEL",
        "gemini-2.5-flash"
    ),

    # =====================================================
    # API
    # =====================================================
    deepseek_api_key=os.getenv(
        "DEEPSEEK_API_KEY",
        ""
    ),

    deepseek_api_base=os.getenv(
        "DEEPSEEK_API_BASE",
        "https://api.siliconflow.cn/v1"
    ),

    gemini_api_key=os.getenv(
        "GEMINI_API_KEY",
        ""
    ),

    # =====================================================
    # Runtime
    # =====================================================
    debug=_to_bool(
        os.getenv(
            "DEBUG",
            "true"
        )
    ),

    # =====================================================
    # Repo
    # =====================================================
    test_repo_root=os.getenv(
        "TEST_REPO_ROOT",
        "./tests/v3"
    ),

    # =====================================================
    # LLM Resilience
    # =====================================================
    llm_retry_count=int(
        os.getenv(
            "LLM_RETRY_COUNT",
            "3"
        )
    ),

    llm_timeout=int(
        os.getenv(
            "LLM_TIMEOUT",
            "120"
        )
    ),

    llm_backoff_seconds=int(
        os.getenv(
            "LLM_BACKOFF_SECONDS",
            "3"
        )
    )
)