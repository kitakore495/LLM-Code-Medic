import time

from typing import (
    List,
    Optional
)

from langchain_core.messages import (
    BaseMessage
)

from src.llm.model_factory import (
    ModelFactory
)

from src.llm.provider_router import (
    ProviderRouter
)

from src.config.runtime_config import (
    runtime_config
)


class LLMInvoker:

    # =========================================================
    # Public Invoke
    # =========================================================
    @staticmethod
    def invoke(
        provider: str,
        model_name: str,
        messages: List[BaseMessage],
        temperature: float = 0.2,
        fallback_provider: Optional[str] = None,
        fallback_model: Optional[str] = None,
        allow_fallback: bool = True
    ):

        retry_count = (
            runtime_config
            .llm_retry_count
        )

        retry_delay = (
            runtime_config
            .llm_backoff_seconds
        )

        try:

            return (
                LLMInvoker
                ._invoke_with_retry(
                    provider=provider,
                    model_name=model_name,
                    messages=messages,
                    temperature=temperature,
                    retry_count=retry_count,
                    retry_delay=retry_delay
                )
            )

        except Exception as e:

            print(
                "\n⚠️ [LLMInvoker] "
                "主模型调用失败"
            )

            print(
                f"⚠️ Provider: "
                f"{provider}"
            )

            print(
                f"⚠️ Model: "
                f"{model_name}"
            )

            print(
                f"⚠️ Error: "
                f"{str(e)}"
            )

            if not allow_fallback:

                raise e

            # =================================================
            # Fallback Provider
            # =================================================
            if not fallback_provider:

                fallback_provider = (
                    ProviderRouter
                    .get_dynamic_fallback_provider(
                        current_provider=provider
                    )
                )

            # =================================================
            # Fallback Model
            # =================================================
            if not fallback_model:

                fallback_model = (
                    ProviderRouter
                    .get_dynamic_fallback_model(
                        provider=fallback_provider
                    )
                )

            try:

                print(
                    "\n🔁 [LLMInvoker] "
                    "开始执行 Fallback..."
                )

                print(
                    f"🧠 Fallback Provider: "
                    f"{fallback_provider}"
                )

                print(
                    f"🧠 Fallback Model: "
                    f"{fallback_model}"
                )

                return (
                    LLMInvoker
                    ._invoke_with_retry(
                        provider=fallback_provider,
                        model_name=fallback_model,
                        messages=messages,
                        temperature=temperature,
                        retry_count=retry_count,
                        retry_delay=retry_delay
                    )
                )

            except Exception as fallback_error:

                print(
                    "\n❌ [LLMInvoker] "
                    "Fallback 调用失败"
                )

                print(
                    f"❌ Error: "
                    f"{str(fallback_error)}"
                )

                raise fallback_error

    # =========================================================
    # Retry Layer
    # =========================================================
    @staticmethod
    def _invoke_with_retry(
        provider: str,
        model_name: str,
        messages: List[BaseMessage],
        temperature: float,
        retry_count: int,
        retry_delay: int
    ):

        last_error = None

        for attempt in range(
            retry_count
        ):

            try:

                llm = (
                    ModelFactory
                    .create_llm(
                        provider=provider,
                        model_name=model_name,
                        temperature=temperature
                    )
                )

                response = (
                    llm.invoke(
                        messages
                    )
                )

                return response

            except Exception as e:

                last_error = e

                print(
                    f"\n⚠️ [LLMInvoker] "
                    f"调用失败 "
                    f"({attempt + 1}"
                    f"/{retry_count})"
                )

                print(
                    f"⚠️ Error: "
                    f"{str(e)}"
                )

                if (
                    attempt
                    <
                    retry_count - 1
                ):

                    print(
                        f"⏳ "
                        f"{retry_delay}s "
                        "后重试..."
                    )

                    time.sleep(
                        retry_delay
                    )

        raise last_error