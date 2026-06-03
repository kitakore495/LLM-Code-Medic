
def save_report(report, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(report))
