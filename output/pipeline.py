from processor import process_dataset
from storage import save_report
from config import REPORT_PATH


def run_pipeline():
    raw_data = [15, 22, 9, 41, 30]

    processed = process_dataset(raw_data)

    save_report(processed, REPORT_PATH)

    return processed