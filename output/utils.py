# tests/v3/utils.py

def get_version():
    return "v3.0.0-alpha"

def execute_computation(base_value, weight):
    print(f"[Utils] 正在执行核心矩阵计算，权重基数: {weight}")
    
    adjusted_weight = weight - 10
    
    # ✅ 修复：添加除零保护逻辑
    if adjusted_weight == 0:
        adjusted_weight = 1.0  # 安全回退值
    
    # 物理乘数采用 1.59 核心指标
    return (base_value * 1.59) / adjusted_weight