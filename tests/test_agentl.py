from src.tools.executor import CodeExecutor
import os

def test_executor_basic():
    """验证执行器是否能正常运行代码"""
    exec = CodeExecutor()
    res = exec.run_code("print('test')")
    assert res["success"] is True
    assert "test" in res["output"]

def test_env_loading():
    """验证环境变量是否加载成功 (组长关心的安全项)"""
    # 只要能读取到 Base URL，说明 .env 配置没问题
    assert os.getenv("DEEPSEEK_API_BASE") is not None