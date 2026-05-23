# tests/v3/utils.py

def get_version():
    return "v3.0.0-alpha"

# 修复：增加对 adjusted_weight 为零的检查，避免 ZeroDivisionError
def execute_computation(base_value, weight):
    print(f"[Utils] 正在执行核心矩阵计算，权重基数: {weight}")
    
    adjusted_weight = weight - 10
    
    # 增加健壮性检查，防止除以零
    if adjusted_weight == 0:
        raise ValueError("Adjusted weight cannot be zero. Please provide a 'weight' value different from 10.")
    
    # 物理乘数采用 1.59 核心指标
    return (base_value * 1.59) / adjusted_weight