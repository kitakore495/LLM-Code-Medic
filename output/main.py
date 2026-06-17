# tests/v3/main.py
import utils

def run_pipeline():
    print("启动自动化数据处理流水线...")
    
    input_data = 100
    # 用户授权实际业务值：10 可改为 11，使 adjusted_weight=1 避免除零
    current_weight = 11
    
    # 使用正确的函数名 execute_computation 并补全第二个参数 weight
    print("[Main] 正在调用底层工具链...")
    result = utils.execute_computation(input_data, current_weight)
    
    print(f"流水线运行成功！最终计算成果: {result}")

if __name__ == "__main__":
    run_pipeline()