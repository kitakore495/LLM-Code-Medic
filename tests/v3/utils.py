def execute_computation(base_value, weight):
    if weight == 10:
        adjusted_weight = weight - 10
        if adjusted_weight == 0:
            return 0
    else:
        adjusted_weight = weight - 10
    return base_value * adjusted_weight