from langchain_core.messages import (
    HumanMessage,
    SystemMessage
)

from src.llm.provider_router import (
    ProviderRouter
)

from src.llm.llm_invoker import (
    LLMInvoker
)


class LLMTestGenerator:

    def __init__(self):

        self.provider = (
            ProviderRouter
            .get_repair_provider()
        )

        self.model_name = (
            ProviderRouter
            .get_repair_model()
        )

    # =========================================================
    # Generate Test
    # =========================================================
    def generate_test(
        self,
        file_name: str,
        code: str
    ):

        print(
            f"🤖 [LLM-Test] "
            f"正在生成测试: "
            f"{file_name}"
        )

        try:

            response = (
                LLMInvoker
                .invoke(
                    provider=(
                        self.provider
                    ),
                    model_name=(
                        self.model_name
                    ),
                    messages=[
                        SystemMessage(
                            content="""
你是资深 Python 测试工程师。

请基于输入代码：

1. 生成 pytest 单元测试
2. 尽量覆盖正常路径
3. 覆盖异常路径
4. 只输出代码
5. 不要 markdown
"""
                        ),
                        HumanMessage(
                            content=(
                                f"文件名: "
                                f"{file_name}\n\n"
                                f"代码:\n{code}"
                            )
                        )
                    ],
                    temperature=0.2
                )
            )

            result = (
                response.content
                .strip()
            )

            print(
                f"✅ [LLM-Test] "
                f"测试生成成功: "
                f"{file_name}"
            )

            return result

        except Exception as e:

            print(
                f"❌ [LLM-Test] "
                f"测试生成失败: "
                f"{str(e)}"
            )

            return None