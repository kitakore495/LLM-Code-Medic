# tests/mock_repo/main.py

# 模拟一个可能存在的导入问题
from utils import add  

def run_task():
    print("正在启动任务...")
    # 错误：utils 模块里没有 add 函数，只有 add_numbers
    result = add(10, 20)
    print(f"计算结果是: {result}")

if __name__ == "__main__":
    run_task()