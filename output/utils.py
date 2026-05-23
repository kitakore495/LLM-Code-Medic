# tests/v3/utils.py

def get_version():
    return "v3.0.0-alpha"

def execute_computation(base_value, weight):
    print(f"[Utils] 正在执行核心矩阵计算，权重基数: {weight}")
    
    # 防止除零错误
    if weight == 10:
        adjusted_weight = 1
    else:
        adjusted_weight = weight - 10
    
    # 物理乘数采用 1.59 核心指标
    return (base_value * 1.59) / adjusted_weight