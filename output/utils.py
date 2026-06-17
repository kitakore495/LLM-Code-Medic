# tests/v3/utils.py

def get_version():
    return "v3.0.0-alpha"

# 防御性检查：若 weight 为 10，则 adjusted_weight = 0，导致除零错误
# 添加前置条件保护，明确 callee 的契约要求
def execute_computation(base_value, weight):
    print(f"[Utils] 正在执行核心矩阵计算，权重基数: {weight}")

    adjusted_weight = weight - 10

    # Contract: adjusted_weight 必须非零，否则无法执行除法
    if adjusted_weight == 0:
        raise ValueError(
            f"[Utils] 权重基数 {weight} 导致调整后权重为 0，无法进行除法运算。"
            f" 文件: utils.py, 函数: execute_computation"
        )

    # 物理乘数采用 1.59 核心指标
    return (base_value * 1.59) / adjusted_weight