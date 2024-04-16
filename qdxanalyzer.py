import sys
import shutil
import time
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import cv2
import numpy as np

#################################################
#
# QDX file format for the Galaxy 1:
#
# header:           JieHe,{LH},4000,8000,2,030,0,FA    LH=layer height
# for each layer repeated:
#   layer number:     int
#   for each layer thumbnail line that contains data:
#      same as print data, but picked one line every 10 and displacement scaled down by 10 for a 800 x 400 thumbnail
#   separator:        "FB"
#   for each layer print line that contains data:
#      int triplets (row, displacement, laser_on)
#   separator:        "FC"
#   separator:        "FD"
#   recap data:     total_layer_number|???
#
################################################# 

start_layer = 0
end_layer = 8000 # Max layer number
do_video = False
do_pictures = False
visuals = False

# Record the start time
start_time = time.time()

LH, X, Y = 50, 4000, 8000                               # Expected values for Galaxy 1
expected_header = f"JieHe,{LH},{X},{Y},2,030,0,FA"      # Galaxy 1
error_layers = []

def vlog(msg):
  #Prints timestamp and text
  print(f"{datetime.fromtimestamp(time.time()-start_time).strftime('%H:%M:%S')} - {msg}")

def validate_file_structure(filename):
    try:
        vlog("Opening and reading the file...")
        with open(filename, 'r') as file:
            first_line = file.readline()

            # Validate header
            vlog("Validating header...")
            header = first_line.strip()
            if header == expected_header:
                vlog(f"Header is compliant: found {header}")
            else:
                vlog(f"!!! Header compliance failed: found {header}")

            if end_layer > start_layer:
                # We want to store the images in a directory
                if do_pictures:
                    # Check if the directory exists
                    if os.path.exists(dir_path):
                        # Remove all contents of the directory
                        shutil.rmtree(dir_path)                
                    # Create the directory
                    os.makedirs(dir_path, exist_ok=True)

                # We want to create the video
                if do_video:
                    # Define the codec and create VideoWriter object
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 'XVID' or 'mp4v'
                    out = cv2.VideoWriter(f"{dir_path}.mp4", fourcc, 24, (Y, X))

                if visuals:
                    vlog("Initialize the frame buffer")
                    # Create an empty (black) image
                    image = np.zeros((4000, 8000, 3), dtype=np.uint8)

            layer_count = 0
            current_layer = 0
            in_layer = False
            
            if start_layer > 3:
                vlog(f"Seeking layer {start_layer}...")
            for line in file:
                line = line.strip()

                if line.isdigit():
                    current_layer = int(line)
                    if current_layer > end_layer:
                        break
                    layer_count += 1
                    if layer_count != current_layer:
                        vlog(f"Error in layer {current_layer}: layer number doesn't match the sequence {layer_count}")
                
                elif line == "FB":
                    if start_layer <= current_layer < end_layer:
                        # Start the analysis of the layer image data between "FB" and "FC"
                        in_layer = True
                        last_row = -1
                        error_flag = False
                        if visuals:
                            # Clear the frame (fill it with black)")
                            image[:] = [0, 0, 0]
                        # Progress bar visualization
                        if current_layer % 50:
                            i = current_layer % 50 + 1
                            iz = start_layer % 50
                            if current_layer - start_layer <= 50 - iz:
                                bar = '-' * iz + '#' * (i-iz) + '-' * (50 - i)
                            else:
                                bar = '#' * i + '-' * (50 - i)
                            print(f'\r[{bar}] {current_layer + 1}', end=' ')
                        else:
                            vlog(f"Processing layer {current_layer}")

                elif line == "FC" and in_layer:
                    # End of the analysis of the layer image data between "FB" and "FC"
                    in_layer = False
                    if error_flag:
                        # This layer had a slicing issue
                        error_layers.append(current_layer)
                        error_flag = False

                    if visuals:
                        cv2.putText(image, f"{current_layer}", (100,300), cv2.FONT_HERSHEY_SIMPLEX, 10, (255,255,255), 20)
                        if do_pictures:
                            cv2.imwrite(f"{dir_path}/layer{current_layer}.png", image)
                        if do_video:
                            out.write(image)

                elif line == "FD":
                    # No more layers
                    break

                elif in_layer:
                    # Data line processing
                    parts = line.split(',')
                    if len(parts) == 3:  # Row data line
                        row, segment_length, laser_on = map(int, parts)

                        # First triplet of a row of segments
                        if row != last_row:
                            segment_start = 0
                        
                        # Coordinate end of the segment to draw
                        segment_end = segment_start + segment_length

                        if segment_end > X:
                            vlog(f"\nError in layer {current_layer}: row {row} exceeds limits. Laser X gets up to {segment_end}")
                            segment_end = X
                            laser_on = 1
                            error_flag = True
                            if visuals:
                                to_fill = (0, 0, 255) # Draw in red
                        elif visuals:
                            to_fill = (255, 255, 255) # Draw in white

                        if visuals and laser_on == 1:
                            if current_layer %2 == 1: # Every other layer is mirrored
                                cv2.line(image, (row, segment_start), (row, segment_end), to_fill, 1)
                            else:
                                cv2.line(image, (Y - row, segment_start), (Y - row, segment_end), to_fill, 1)
                        last_row = row 
                        segment_start = segment_end

            if '|' in line:
                print(f'\r[{bar}] {current_layer}', end=' ')
                vlog(f"Processing layer {current_layer}")
            else:
                vlog(f"Processing layer {current_layer-1}")

            if len(error_layers) > 0:
                print("Errors in the following layers:")
                print(*error_layers)
            else:
                print("No errors found in the layers")

            if '|' in line:
                # End of the file reached: validate recap section, reading the last line of the file
                recap = line.split('|')
                if len(recap) == 2:
                    total_layers_reported = int(recap[0])
                    vlog("Validating recap section...")
                    if layer_count == total_layers_reported:
                        vlog(f"Recap is compliant: found {layer_count} layers, expected {total_layers_reported}.")
                    else:
                        vlog(f"Recap compliance failed: found {layer_count} layers, expected {total_layers_reported}.")

            if do_video:
                out.release()
                vlog(f"Video {dir_path}.mp4 released")

            if do_pictures:
                vlog(f"Pictures available in the {dir_path} folder")
                
    except FileNotFoundError:
        vlog(f"Error: The file '{filename}' was not found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("QDX Analyzer")
        print("Usage: python qdxanalyzer.py <filename> <optional end-layer> <optional start-layer>  <optional p|v>")
        print("     <filename>: the qdx file")
        print("     <optional end layer>: default is 8000, which is the maximum possible")
        print("     <optional start layer>: default is 0, which is the beginning of the file")
        print("     <optional p|v>: p indicates pictures, v indicates video, pv indicates both (slower execution)")
        print("                     pictures are stored in a separate folder named after the filename")
        print("                     if omitted only the analisys will be performed")
        sys.exit(1)

    filename = sys.argv[1]
    dir_path = Path(filename).stem 
    if len(sys.argv) > 2:
        end_layer = int(sys.argv[2])
    if len(sys.argv) > 3:
        start_layer = int(sys.argv[3])
    if len(sys.argv) > 4:
        if 'v' in sys.argv[4]:
            do_video = True
        if 'p' in sys.argv[4]:
            do_pictures = True
        visuals = do_pictures or do_video

    vlog(f"Start analisys for {filename}, start layer {start_layer}, end layer {end_layer}")
    if visuals:
        vlog(f"Generate{" pictures" if do_pictures else ""}{" video" if do_video else ""}")
    validate_file_structure(filename)
    vlog("Finished")
