from validator import validate_dataset
from metrics import calculate_score


def process_dataset(data):
    validated = validate_dataset(data)

    result = calculate_score(validated)

    return result