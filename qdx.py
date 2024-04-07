import argparse
import os
import numpy as np
from PIL import Image

# Step 1: Parsing Command Line Arguments
parser = argparse.ArgumentParser(description="Process PNG images in a folder.")
parser.add_argument('layer_height', type=int, help="The layer height as an integer.")
parser.add_argument('png_folder', type=str, help="The path to the folder containing PNG images.")
args = parser.parse_args()

layer_height = args.layer_height
png_folder = args.png_folder

# Step 2: Checking the PNG Files in the Folder
png_files = [f for f in os.listdir(png_folder) if f.endswith('.png')]
if not png_files:
    raise ValueError("No PNG files found in the specified folder.")

# Check dimensions
first_image = Image.open(os.path.join(png_folder, png_files[0]))
png_w, png_h = first_image.size
for f in png_files[1:]:
    with Image.open(os.path.join(png_folder, f)) as img:
        if img.size != (png_w, png_h):
            raise ValueError("Not all PNG images have the same dimensions.")

# Step 3: Creating the "qdx.qdx" File and Writing Initial Data
with open("qdx.qdx", "w") as qdx_file:
    qdx_file.write(f"JieHe,LH,{layer_height},8000,2,030,0,FA\n")

# Step 4: Creating and Manipulating the Matrix
matrix = np.zeros((4000, 8000), dtype=np.byte)

# Step 5: Processing Each PNG File
for png_file in sorted(png_files):
    img_path = os.path.join(png_folder, png_file)
    with Image.open(img_path) as img:
        img_array = np.asarray(img.convert('1')).astype(np.byte)  # Convert to black & white and then to numpy array
        # Center the image in the matrix
        x_offset = (8000 - png_w) // 2
        y_offset = (4000 - png_h) // 2
        matrix[y_offset:y_offset+png_h, x_offset:x_offset+png_w] = img_array

        with open("qdx.qdx", "a") as qdx_file:
            # Step 6: Processing columns in the matrix
            for col in range(8000):
                last_val = matrix[0, col]
                count = 1
                for row in range(1, 4000):
                    if matrix[row, col] == last_val:
                        count += 1
                    else:
                        qdx_file.write(f"{col},{count},{last_val}\n")
                        count = 1
                        last_val = matrix[row, col]
                # For the last segment in each column
                qdx_file.write(f"{col},{count},{last_val}\n")
            qdx_file.write("FB\n")
