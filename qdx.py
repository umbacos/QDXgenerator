import sys
import os
import time
from PIL import Image
import numpy as np

def vlog(text):
    print(f"{current_time()}: {text}")

def current_time():
    """Return the current time in HH:MM:SS format."""
    return time.strftime("%H:%M:%S")

def validate_png_files(folder_path):
    vlog("Check that all files in the folder are PNGs with the same dimensions.")
    png_files = [f for f in os.listdir(folder_path) if f.endswith('.png')]
    if not png_files:
        raise ValueError("No PNG files found in the specified folder.")
    
    first_image = Image.open(os.path.join(folder_path, png_files[0]))
    first_size = first_image.size
    for file in png_files[1:]:
        image = Image.open(os.path.join(folder_path, file))
        if image.size != first_size:
            raise ValueError("PNG files have differing dimensions.")
    return png_files, first_size

def process_images(png_folder, png_files, layer_height, png_dimensions):
    vlog("Process each PNG file and perform the required operations.")
    main_img_size = (4000,8000)
    thumb_img_size = (400, 800)
    main_img = np.zeros(main_img_size, dtype=np.uint8)
    thumb_img = np.zeros(thumb_img_size, dtype=np.uint8)

    with open("qdx.qdx", "w") as qdx_file:
        qdx_file.write(f"JieHe,{layer_height},4000,8000,2,030,0,FA\n")
        
        for counter, file_name in enumerate(sorted(png_files), 1):
            vlog("Processing {file_name} ({counter}/{len(png_files)})")
            image_path = os.path.join(png_folder, file_name)
            image = Image.open(image_path).convert("L")
            # Scale and center the main image
            centered_main = center_image(np.where(np.array(image) < 128, 0, 1), main_img.shape)
            # Scale down by factor of 10 and center the thumbnail image
            thumb_scaled = image.resize((png_dimensions[0] // 10, png_dimensions[1] // 10))
            centered_thumb = center_image(np.where(np.array(thumb_scaled) < 128, 0, 1), thumb_img.shape)

            write_image_data(qdx_file, centered_main, centered_thumb, counter)

        qdx_file.write("FD\n")
        qdx_file.write(f"{counter}|1234\n")


def center_image(img_array, target_size):
    vlog("Center img_array within a target_size array of zeros.")
    centered_array = np.zeros(target_size, dtype=np.uint8)
    y_offset = (target_size[0] - img_array.shape[0]) // 2
    x_offset = (target_size[1] - img_array.shape[1]) // 2
    centered_array[y_offset:y_offset+img_array.shape[0], x_offset:x_offset+img_array.shape[1]] = img_array
    return centered_array

def write_image_data(qdx_file, main_img, thumb_img, counter):
    vlog("Write the processed data of an image to the qdx file.")
    qdx_file.write(f"{counter}\n")
    # Thumb image processing
    write_triplets(thumb_img, qdx_file)
    qdx_file.write("FB\n")
    # Main image processing
    write_triplets(main_img, qdx_file)
    qdx_file.write("FC\n")
    vlog("done")

def write_triplets(img, qdx_file):
    vlog("Write triplets for each column change in img to qdx_file.")
    for column in range(img.shape[1]):
        prev_val = img[0, column]
        count = 1
        for row in range(1, img.shape[0]):
            if img[row, column] == prev_val:
                count += 1
            else:
                if count != img.shape[0]:
                    qdx_file.write(f"{column},{count},{prev_val}\n")
                prev_val = img[row, column]
                count = 1
        # Process the last segment
        if count != img.shape[0]:
            qdx_file.write(f"{column},{count},{prev_val}\n")
    vlog("done.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: script.py <layer_height> <png_folder>")
        sys.exit(1)

    layer_height = int(sys.argv[1])
    png_folder = sys.argv[2]

    try:
        png_files, png_dimensions = validate_png_files(png_folder)
        process_images(png_folder, png_files, layer_height, png_dimensions)
        vlog("Successfully processed all images.")
    except Exception as e:
        print(f"Error: {e}")
