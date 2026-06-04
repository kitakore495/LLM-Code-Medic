# tests/v3/utils.py

_PHYSICAL_MULTIPLIER = 1.59  # 核心物理乘数指标
_MIN_WEIGHT_EXCLUSIVE = 10  # 调整后的权重必须 > 0

def get_version():
    return "v3.0.0-alpha"

def execute_computation(base_value, weight):
    """执行核心矩阵计算
    
    Args:
        base_value: 基础计算值
        weight: 权重值 (必须 > 10)
    
    Returns:
        计算结果
    
    Raises:
        ValueError: 如果 weight <= 10 导致调整后的权重无效
    """
    print(f"[Utils] 正在执行核心矩阵计算，权重基数: {weight}")
    
    if weight <= _MIN_WEIGHT_EXCLUSIVE:
        raise ValueError(
            f"无效权重 {weight}: 必须 > {_MIN_WEIGHT_EXCLUSIVE} "
            f"(utils.execute_computation)"
        )
    
    adjusted_weight = weight - _MIN_WEIGHT_EXCLUSIVE
    return (base_value * _PHYSICAL_MULTIPLIER) / adjusted_weight