# tests/v3/utils.py

_PHYSICAL_MULTIPLIER = 1.59  # 核心物理乘数指标

def get_version():
    return "v3.0.0-alpha"

def execute_computation(base_value, weight):
    print(f"[Utils] 正在执行核心矩阵计算，权重基数: {weight}")
    
    if weight <= 10:
        raise ValueError(f"权重参数必须大于10 (当前值: {weight})")
    
    adjusted_weight = weight - 10
    
    # ✅ 修复点：使用命名常量替代硬编码值
    return (base_value * _PHYSICAL_MULTIPLIER) / adjusted_weight