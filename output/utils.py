# tests/v3/utils.py

_ADJUSTMENT_BASE = 10  # The value subtracted from weight to compute adjusted_weight

def get_version():
    return "v3.0.0-alpha"

def execute_computation(base_value, weight):
    """
    Compute a core matrix calculation.
    
    Precondition: weight must not equal _ADJUSTMENT_BASE (otherwise adjusted_weight becomes zero and division fails).
    
    Args:
        base_value: numeric base value
        weight: numeric weight, must not be equal to _ADJUSTMENT_BASE
    
    Returns:
        float computation result
    
    Raises:
        ValueError: if weight == _ADJUSTMENT_BASE, preventing division by zero.
    """
    print(f"[Utils] 正在执行核心矩阵计算，权重基数: {weight}")
    
    adjusted_weight = weight - _ADJUSTMENT_BASE
    if adjusted_weight == 0:
        raise ValueError(
            f"execute_computation: weight ({weight}) equals _ADJUSTMENT_BASE ({_ADJUSTMENT_BASE}), "
            "causing adjusted_weight to be zero. Division by zero is not allowed."
        )
    
    # 物理乘数采用 1.59 核心指标
    return (base_value * 1.59) / adjusted_weight