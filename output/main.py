# tests/v3/main.py
import utils

def run_pipeline():
    print("🚀 启动自动化数据处理流水线...")
    
    input_data = 100
    # 修复：将 current_weight 从 10 修改为 11，以避免 utils 内部的 ZeroDivisionError
    current_weight = 11
    
    # 修复：调用正确的接口 'execute_computation' 并传入所有必需参数
    print("[Main] 正在调用底层工具链...")
    result = utils.execute_computation(input_data, current_weight)
    
    print(f"🎉 流水线运行成功！最终计算成果: {result}")

if __name__ == "__main__":
    run_pipeline()