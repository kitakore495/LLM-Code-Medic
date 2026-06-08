from validator import validate_dataset

# 修复：修正模块名和函数名
from metrics import calculate_score


def process_dataset(data):
    validated = validate_dataset(data)

    result = calculate_score(validated)

    return result