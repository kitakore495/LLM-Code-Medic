def calculate_score(values):
    avg = sum(values) / len(values)

    return {
        "average": avg,
        "max": max(values),
        "min": min(values),
    }