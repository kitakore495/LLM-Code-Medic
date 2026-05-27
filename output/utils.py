# tests/v3/utils.py

def get_version():
    return "v3.0.0-alpha"

def execute_computation(base_value, weight):
    print(f"[Utils] 正在执行核心矩阵计算，权重基数: {weight}")
    
    if weight <= 10:
        raise ValueError("权重值必须大于10")
    
    adjusted_weight = weight - 5  # 调整分母计算方式避免过小值
    
    # 物理乘数采用 1.59 核心指标
    return (base_value * 1.59) / adjusted_weight