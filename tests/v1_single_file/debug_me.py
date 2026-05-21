# debug_me.py

def calculate_sum(a, b):
    # 错误 1: result 写成了 reslt
    reslt = a + b
    return result

def main():
    print("开始计算...")
    # 错误 2: 字符串未闭合或逻辑错误（这里写个明显的语法错误）
    val = calculate_sum(10, 20)
    print(f"结果是: {val}")

if __name__ == "__main__":
    main()