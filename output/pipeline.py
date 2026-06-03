from processor import process_dataset
from storage import save_report
import config


def run_pipeline():
    raw_data = [15, 22, 9, 41, 30]

    processed = process_dataset(raw_data)

    save_report(processed, path=config.REPORT_PATH)

    return processed