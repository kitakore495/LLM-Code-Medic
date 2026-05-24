# tests/v3/utils.py

def get_version():
    return "v3.0.0-alpha"

# 漏洞点 1：老函数名被改成了 'execute_computation'
# 漏洞点 2：隐藏了逻辑漏洞，若 weight 传入 10，则 adjusted_weight 为 0，触发 ZeroDivisionError
def execute_computation(base_value, weight):
    print(f"[Utils] 正在执行核心矩阵计算，权重基数: {weight}")
    
    # 当 weight == 10 时，这里会变成 0
    adjusted_weight = weight - 10
    
    # 物理乘数采用 1.59 核心指标
    return (base_value * 1.59) / adjusted_weight