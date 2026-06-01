# tests/v3/main.py
import utils

def run_pipeline():
    print("🚀 启动自动化数据处理流水线...")
    
    input_data = 100
    # 根据业务逻辑，weight应该从配置或输入获取
    # 当前硬编码的10违反契约，但无上下文确定正确值
    # 需要业务方提供合法输入
    raise ValueError(
        "ESCALATE_REQUIRED: current_weight=10 violates utils.execute_computation's "
        "contract (weight > 10). No valid value can be derived from context. "
        "Please provide the correct weight value from business requirements."
    )
    
    print("[Main] 正在调用底层工具链...")
    result = utils.execute_computation(input_data, current_weight)
    
    print(f"🎉 流水线运行成功！最终计算成果: {result}")

if __name__ == "__main__":
    run_pipeline()