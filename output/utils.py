def get_version():
    return "v3.0.0-alpha"

def execute_computation(base_value, weight):
    print(f"[Utils] 正在执行核心矩阵计算，权重基数: {weight}")
    
    if weight == 10:
        raise ValueError("权重值不能为10")
    
    adjusted_weight = weight - 10 if weight != 10 else 1
    
    return (base_value * 1.59) / adjusted_weight
