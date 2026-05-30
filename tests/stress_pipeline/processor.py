



from validator import validate_dataset

# ❌ bug: import 名写错
from metric import compute_metrics


def process_dataset(data):
    validated = validate_dataset(data)

    result = compute_metrics(validated)

    return result

