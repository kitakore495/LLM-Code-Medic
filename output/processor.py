from validator import validate_dataset

# ✅ fix: corrected import name to match actual function in metrics.py
from metrics import calculate_score


def process_dataset(data):
    validated = validate_dataset(data)

    result = calculate_score(validated)

    return result