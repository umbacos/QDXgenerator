def count_lines_ending_with_comma_one_between_markers(file_path):
    count = 0
    within_block = False
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if 'FB' in line:
                within_block = True
            elif 'FC' in line:
                within_block = False
#            elif within_block and line.endswith(",1"):
            elif line.endswith(",1"):
                count += 1
    return count

# Replace 'your_file_path_here.txt' with the path to your actual file
file_path = 'batmarang.qdx'
count_result = count_lines_ending_with_comma_one_between_markers(file_path)
print(f"Number of lines ending with ',1' between 'FB' and 'FC': {count_result}")
