from utils import execute_computation

def main():
    input_data = 100
    current_weight = 10
    result = execute_computation(input_data, current_weight)
    print(f"Result: {result}")

if __name__ == "__main__":
    main()