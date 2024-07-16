import sys
import os
import time
from PIL import Image
import numpy as np

def help():
    print("Usage: script.py [-c] [layer_height] <png_folder>")
    print("       -c OPTIONAL, check only, no output file generated")
    print("       layer_height OPTIONAL")
    print("       <png_folder> REQUIRED")
    sys.exit(1)

def vlog(text):
    print(f"{current_time()}: {text}")

def current_time():
    """Return the current time in HH:MM:SS format."""
    return time.strftime("%H:%M:%S")

def read_parameters(argv):
    if len(sys.argv) < 2:
        help()

    layer_height = 50
    png_folder = ""
    check_only = False

    # Read command line parameters:
    for index, arg in enumerate(argv[1:]):
        
        # layer_height
        if arg.isdigit():
            layer_height = int(arg)

        # Found a visualization to generate
        elif "-c" == arg:
            check_only = True
         
        # Filename
        elif os.path.isdir(arg):
            png_folder = arg
        else:
            print(f"Error: The directory '{arg}' was not found.")
            help()

    if png_folder == "":
        help()     
            
    print(f"Running {sys.argv[0]} with the following parameters:")
    print(f"   Input folder: {png_folder}")
    print(f"   Layer heoght: {layer_height}")
    print(f"   Check only:   {check_only}")

    return layer_height, png_folder, check_only


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

def process_images(png_folder, png_files, layer_height, png_dimensions, check_only):
    vlog("Process each PNG file and perform the required operations.")
    main_img_size = (4000,8000)
    thumb_img_size = (400, 800)
    main_img = np.zeros(main_img_size, dtype=np.uint8)
    thumb_img = np.zeros(thumb_img_size, dtype=np.uint8)
    triplets = 0

    if check_only:
        qdx_file = ""
    else:
        qdx_file = open(png_folder + ".qdx", "w")
        qdx_file.write(f"JieHe,{layer_height},4000,8000,2,030,0,FA\n")
    
    for counter, file_name in enumerate(sorted(png_files), 1):
        vlog("Processing " + file_name + " (" + str(counter) + "/" + str(len(png_files)) + ")")
        image_path = os.path.join(png_folder, file_name)
        image = Image.open(image_path).convert("L")
        # Scale and center the main image
        centered_main = center_image(np.where(np.array(image) < 128, 0, 1), main_img.shape)
        # Scale down by factor of 10 and center the thumbnail image
        thumb_scaled = image.resize((png_dimensions[0] // 10, png_dimensions[1] // 10))
        centered_thumb = center_image(np.where(np.array(thumb_scaled) < 128, 0, 1), thumb_img.shape)

        triplets += write_image_data(qdx_file, centered_main, centered_thumb, counter, check_only)
        vlog(f"Done. Total triplets: {triplets}")

    if not check_only:
        qdx_file.write("FD\n")
        qdx_file.write(f"{counter}|{triplets + counter * 2}\n")
    vlog(f"Recap FD: {counter}|{triplets + counter * 2}")


def center_image(img_array, target_size):
    vlog(f"Center img_array within a {target_size} array of zeros.")
    centered_array = np.zeros(target_size, dtype=np.uint8)
    y_offset = (target_size[0] - img_array.shape[0]) // 2
    x_offset = (target_size[1] - img_array.shape[1]) // 2
    centered_array[y_offset:y_offset+img_array.shape[0], x_offset:x_offset+img_array.shape[1]] = img_array
    return centered_array

def write_image_data(qdx_file, main_img, thumb_img, counter, check_only):
    triplets = 0
    if not check_only: 
        vlog("Write the processed data of an image to the qdx file.")
        qdx_file.write(f"{counter}\n")
    vlog("Thumb image processing")
    triplets += write_triplets(thumb_img, qdx_file, check_only)
    if not check_only: 
        qdx_file.write("FB\n")
    vlog("Main image processing")
    triplets += write_triplets(main_img, qdx_file, check_only)
    if not check_only: 
        qdx_file.write("FC\n")
    return triplets

def write_triplets(img, qdx_file, check_only):
    if check_only:
        vlog("Count triplets for each column change in img.")
    else:
        vlog("Write triplets for each column change in img to the qdx file.")
    triplets = 0
    for column in range(img.shape[1]):
        prev_val = img[0, column]
        count = 1
        for row in range(1, img.shape[0]):
            if img[row, column] == prev_val:
                count += 1
            else:
                if count != img.shape[0]:
                    if not check_only: 
                        qdx_file.write(f"{column},{count},{prev_val}\n")
                    triplets += 1
                prev_val = img[row, column]
                count = 1
        # Process the last segment
        if count != img.shape[0]:
            if not check_only: 
                qdx_file.write(f"{column},{count},{prev_val}\n")
            triplets += 1
    vlog(f"Done. Triplets: {triplets}")
    return triplets

if __name__ == "__main__":
    start_time = current_time()
    try:
        layer_height, png_folder, check_only = read_parameters(sys.argv)
        png_files, png_dimensions = validate_png_files(png_folder)
        process_images(png_folder, png_files, layer_height, png_dimensions, check_only)
        vlog(f"Successfully processed all images since {start_time}")
    except Exception as e:
        print(f"Error: {e}")
