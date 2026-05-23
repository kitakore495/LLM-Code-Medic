import os

from src.llm.model_factory import (
    create_model
)


# =========================================================
# Diagnose LLM
# =========================================================
def get_diagnose_llm():

    provider = os.getenv(
        "DIAGNOSE_PROVIDER",
        "deepseek"
    ).strip().lower()

    model_name = os.getenv(
        "DIAGNOSE_MODEL",
        "deepseek-ai/DeepSeek-R1"
    ).strip()

    print(
        f"🧠 Diagnose Provider: "
        f"{provider}"
    )

    print(
        f"🧠 Diagnose Model: "
        f"{model_name}"
    )

    return create_model(
        provider=provider,
        model_name=model_name,
        temperature=0.2
    )


# =========================================================
# Repair LLM
# =========================================================
def get_repair_llm():

    provider = os.getenv(
        "REPAIR_PROVIDER",
        "deepseek"
    ).strip().lower()

    model_name = os.getenv(
        "REPAIR_MODEL",
        "deepseek-ai/DeepSeek-V3"
    ).strip()

    print(
        f"🧠 Repair Provider: "
        f"{provider}"
    )

    print(
        f"🧠 Repair Model: "
        f"{model_name}"
    )

    return create_model(
        provider=provider,
        model_name=model_name,
        temperature=0.2
    )