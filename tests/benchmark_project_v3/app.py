from pipeline import run_pipeline


def main():
    print("🚀 启动智能分析流水线")
    result = run_pipeline()

    print("✅ 分析完成")
    print(result)


if __name__ == "__main__":
    main()
