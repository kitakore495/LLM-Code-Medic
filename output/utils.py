# tests/v3/utils.py

def get_version():
    return "v3.0.0-alpha"

# 最小权重阈值（排他）
_MIN_WEIGHT_EXCLUSIVE = 10  # weight必须大于10，否则adjusted_weight会<=0

def execute_computation(base_value, weight):
    """执行核心矩阵计算
    
    Args:
        base_value: 基础值
        weight: 权重值，必须大于10
        
    Raises:
        ValueError: 如果weight <= 10
    """
    if weight <= _MIN_WEIGHT_EXCLUSIVE:
        raise ValueError(
            f"权重值必须大于{_MIN_WEIGHT_EXCLUSIVE}，当前值: {weight} "
            f"(utils.py:execute_computation)"
        )
    
    print(f"[Utils] 正在执行核心矩阵计算，权重基数: {weight}")
    
    # 当 weight == 10 时，这里会变成 0
    adjusted_weight = weight - 10
    
    # 物理乘数采用 1.59 核心指标
    return (base_value * 1.59) / adjusted_weight