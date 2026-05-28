# tests/v3/utils.py

def get_version():
    return "v3.0.0-alpha"

# Business constants with explanatory comments
_MIN_WEIGHT_EXCLUSIVE = 10  # weight must be >10 to prevent adjusted_weight <= 0
_PHYSICAL_MULTIPLIER = 1.59  # core physical constant from business requirements

def execute_computation(base_value, weight):
    """Perform core matrix computation.
    
    Args:
        base_value: The base input value
        weight: Must be >10 to ensure positive adjusted_weight
        
    Returns:
        The computed result
        
    Raises:
        ValueError: If weight violates business constraints
    """
    if weight <= _MIN_WEIGHT_EXCLUSIVE:
        raise ValueError(
            f"Invalid weight {weight}: must be > {_MIN_WEIGHT_EXCLUSIVE} "
            f"to prevent division by zero (business constraint)"
        )
    
    print(f"[Utils] 正在执行核心矩阵计算，权重基数: {weight}")
    adjusted_weight = weight - _MIN_WEIGHT_EXCLUSIVE
    return (base_value * _PHYSICAL_MULTIPLIER) / adjusted_weight