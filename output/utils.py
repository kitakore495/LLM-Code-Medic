# tests/v3/utils.py

PHYSICAL_MULTIPLIER = 1.59  # 核心物理乘数指标

def get_version():
    return "v3.0.0-alpha"

def execute_computation(base_value, weight):
    print(f"[Utils] 正在执行核心矩阵计算，权重基数: {weight}")
    
    # 当 weight == 10 时，这里会变成 0
    adjusted_weight = weight - 10
    
    if adjusted_weight == 0:
        raise ValueError(f"无效的权重值: {weight}。调整后的权重不能为零 (weight - 10 = 0)")
    
    return (base_value * PHYSICAL_MULTIPLIER) / adjusted_weight