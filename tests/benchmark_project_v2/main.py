# tests/v3/main.py
import utils

def run_pipeline():
    print("🚀 启动自动化数据处理流水线...")
    
    input_data = 100
    current_weight = 10  # 传入 10 会导致 utils 内部触发除零错误
    
    # ❌ 漏洞点 3：调用了不存在的旧接口 'compute_core_logic'
    # ❌ 漏洞点 4：漏掉了必传参数 'weight'
    print("[Main] 正在调用底层工具链...")
    result = utils.compute_core_logic(input_data)
    
    print(f"🎉 流水线运行成功！最终计算成果: {result}")

if __name__ == "__main__":
    run_pipeline()