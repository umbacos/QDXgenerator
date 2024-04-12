def count_lines_ending_with_comma_one(file_path):
    count = 0
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip().endswith(",1"):
                count += 1
    return count

# Replace 'your_file_path_here.txt' with the path to your actual file
file_path = 'batmarang.qdx'
count_result = count_lines_ending_with_comma_one(file_path)
print(f"Number of lines ending with ',1': {count_result}")
