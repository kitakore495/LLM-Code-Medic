
from processor import process_dataset
from storage import save_report


def run_pipeline():
    raw_data = [15, 22, 9, 41, 30]

    processed = process_dataset(raw_data)

    # ❌ bug: 漏参数
    save_report(processed)

    return processed
