from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

from src.llm.model_factory import (
    ModelFactory
)

from src.llm.provider_router import (
    ProviderRouter
)


class LLMTestGenerator:

    def __init__(self):

        self.system_prompt = """
你是专业 Python 单元测试工程师。

请根据源码生成 pytest 单元测试。

要求：

1. 使用 pytest
2. 覆盖核心逻辑
3. 包含边界情况
4. 返回完整 python 文件
5. 不要解释
6. 不要 markdown
7. 直接输出代码
"""

    # =====================================================
    # Build Main LLM
    # =====================================================
    def _build_llm(self):

        provider = (
            ProviderRouter
            .get_repair_provider()
        )

        model = (
            ProviderRouter
            .get_repair_model()
        )

        return (
            ModelFactory
            .create_llm(
                provider=provider,
                model_name=model
            )
        )

    # =====================================================
    # Build Fallback LLM
    # =====================================================
    def _build_fallback_llm(self):

        provider = (
            ProviderRouter
            .get_fallback_provider()
        )

        model = (
            ProviderRouter
            .get_fallback_model()
        )

        return (
            ModelFactory
            .create_llm(
                provider=provider,
                model_name=model
            )
        )

    # =====================================================
    # Generate Test
    # =====================================================
    def generate_test(
        self,
        file_name: str,
        source_code: str
    ):

        print(
            f"🤖 [LLM-Test] 正在生成测试: "
            f"{file_name}"
        )

        prompt = f"""
目标文件:
{file_name}

源码:

{source_code}

请生成 pytest 单元测试文件。
"""

        try:

            llm = (
                self
                ._build_llm()
            )

            response = llm.invoke(
                [
                    SystemMessage(
                        content=(
                            self
                            .system_prompt
                        )
                    ),
                    HumanMessage(
                        content=prompt
                    )
                ]
            )

        except Exception as e:

            print(
                "⚠️ [LLM-Test] "
                "主模型失败，切换 Fallback..."
            )

            print(
                f"⚠️ Error: {e}"
            )

            try:

                llm = (
                    self
                    ._build_fallback_llm()
                )

                response = llm.invoke(
                    [
                        SystemMessage(
                            content=(
                                self
                                .system_prompt
                            )
                        ),
                        HumanMessage(
                            content=prompt
                        )
                    ]
                )

            except Exception as fallback_error:

                print(
                    f"❌ [LLM-Test] "
                    f"测试生成失败: "
                    f"{fallback_error}"
                )

                return None

        content = response.content

        # =====================================================
        # Gemini sometimes returns list
        # =====================================================
        if isinstance(
            content,
            list
        ):

            content = "\n".join(
                str(x)
                for x in content
            )

        content = str(
            content
        ).strip()

        # =====================================================
        # Remove markdown fences
        # =====================================================
        content = (
            content
            .replace(
                "```python",
                ""
            )
            .replace(
                "```",
                ""
            )
            .strip()
        )

        print(
            f"✅ [LLM-Test] "
            f"测试生成成功: "
            f"{file_name}"
        )

        return content