import utils

def run_pipeline():
    print("🚀 启动自动化数据处理流水线...")
    
    input_data = 100
    current_weight = 9  # 修改为安全值避免除零
    
    print("[Main] 正在调用底层工具链...")
    result = utils.execute_computation(input_data, current_weight)
    
    print(f"🎉 流水线运行成功！最终计算成果: {result}")

if __name__ == "__main__":
    run_pipeline()
