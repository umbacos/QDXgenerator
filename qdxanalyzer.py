import sys
import os
import time
import shutil
import cv2
import numpy as np
from datetime import datetime

#################################################
#
# QDX file format for the Galaxy 1:
#
# header:           JieHe,{LH},{X},{Y},2,030,0,FA    
#                   LH=layer height, X=pixels on the x axis, Y=pixels on the Y axis
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

# Record the start time
start_time = time.time()

# Expected values for Galaxy 1
LH, X, Y, Z = 50, 4000, 8000, 8000  
expected_header = f"JieHe,{LH},{X},{Y},2,030,0,FA"

c_red = (0, 0, 255)
c_white = (255, 255, 255)

def help():
    print("QDX Analyzer")
    print("Usage: python qdxanalyzer.py <filename> <optional end-layer> <optional start-layer>  <optional p|v>")
    print("     <filename>: the qdx file")
    print(f"     <optional end-layer>: default is {Z}, which is the maximum possible")
    print("     <optional start-layer>: default is 1, which is the beginning of the file")
    print("     <optional p|v>: p indicates pictures, v indicates video, pv indicates both (slower execution)")
    print("                     pictures are stored in a separate folder named after the filename")
    print("                     if omitted only the analisys will be performed")
    sys.exit(1)

# Prints timestamp and msg
def vlog(msg):
  print(f"{datetime.fromtimestamp(time.time()-start_time).strftime('%H:%M:%S')} - {msg}")

# Draw a vertical line in the frame buffer
def draw_segment(current_layer, image, row, segment_start, segment_end, color):                                
    if current_layer %2 == 1: # Every other layer is mirrored
        cv2.line(image, (row, segment_start), (row, segment_end), color, 1)
    else:
        cv2.line(image, (Y - row, segment_start), (Y - row, segment_end), color, 1)

def read_parameters(argv):
    if len(argv) < 2:
        help()

    filename = ""
    start_layer = end_layer = 0
    do_video = do_pictures = visuals = False

    # Read command line parameters:
    for index, arg in enumerate(argv[1:]):
        # Filename
        if arg.endswith(".qdx"):
            if os.path.isfile(arg):
                filename = arg
            else:
                print(f"Error: The file '{arg}' was not found.")
                help()

        # Found start or end layer
        # if only one number is provided on the cmd line, it is the end layer
        # if two numbers are provided, they provide the interval to analyze
        elif arg.isdigit():
            if end_layer == 0:
                end_layer = int(arg)
            else:
                start_layer = int(arg)
                if start_layer > end_layer:
                    start_layer, end_layer = end_layer, start_layer

        # Found a visualization to generate
        else:
            if 'p' in arg:
                do_pictures = True 
            if 'v' in arg:
                do_video = True 

    if filename == "":
        help()     
        
    # if not start end are provided on the command line, do the entire file
    if end_layer == 0:
        end_layer == Z    
    if start_layer == 0:
        start_layer == 1
    
    print(f"Running {sys.argv[0]} with the following parameters:")
    print(f"   Input file:   {filename}")
    print(f"   Start layer:  {start_layer}")
    print(f"   End layer:    {end_layer}")
    print(f"   Create images:{"yes" if do_pictures else "no"}")
    print(f"   Create video: {"yes" if do_video else "no"}")

    return filename, start_layer, end_layer, do_video, do_pictures

def validate_file_structure(filename, start_layer, end_layer, do_video, do_pictures):
    
    visuals = do_pictures or do_video    # only if needed, we will creates and manage the frame buffer
    dir_path, _ = os.path.splitext(filename)         

    # We want to store the images in a directory
    if do_pictures:
        # If the directory exists, remove all contents of the directory
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)                
        os.makedirs(dir_path, exist_ok=True)

    # We want to create the video
    if do_video:
        # Define the codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 'XVID' or 'mp4v'
        out = cv2.VideoWriter(f"{dir_path}.mp4", fourcc, 24, (Y, X))

    if visuals:
        vlog("Initialize the frame buffer")
        # Create an empty (black) image
        image = np.zeros((X, Y, 3), dtype=np.uint8)

    layer_count = 0
    current_layer = 0
    in_layer = False
    error_layers = []

    vlog(f"Opening and reading {filename}...")
    with open(filename, 'r') as file:
        first_line = file.readline()

        # Validate header and continue
        vlog("Validating header...")
        header = first_line.strip()
        if header == expected_header:
            vlog(f"Header is compliant: found {header}")
        else:
            vlog(f"!!! Header compliance failed: found {header}")

        # Courtesy message
        if start_layer > 5:
            vlog(f"Seeking layer {start_layer}...")

        # Let's go!!!
        for line in file:
            line = line.strip()

            # Found a layer number that starts the respective layer section
            if line.isdigit():
                current_layer = int(line)
                # Exit criteria
                if current_layer > end_layer:
                    break

                layer_count += 1
                if layer_count != current_layer:
                    vlog(f"Error in layer {current_layer}: layer number doesn't match the sequence {layer_count}")
            
            # Start the analysis of the layer image data between "FB" and "FC"
            elif line == "FB":
                # If the layer is in the analysis interval, let's get into it
                if current_layer >= start_layer:
                    in_layer = True
                    last_row = -1
                    segment_end = X
                    error_flag = False
                    # Clear the frame buffer (fill it with black)
                    if visuals:
                        image[:] = [0, 0, 0]
                    # Progress bar visualization (done once per layer)
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

            # End of the analysis of the layer image data between "FB" and "FC"
            elif line == "FC" and in_layer:
                in_layer = False
                
                if error_flag:
                    # This layer had a slicing issue, add it to the list
                    error_layers.append(current_layer)
                    error_flag = False
                if visuals:
                    # Stamp the layer number on the frame
                    cv2.putText(image, f"{current_layer}", (100,300), cv2.FONT_HERSHEY_SIMPLEX, 10, (255,255,255), 20)
                    if do_pictures:
                        # Dump the image in the directory
                        cv2.imwrite(f"{dir_path}/layer{current_layer}.png", image)
                    if do_video:
                        # add the frame to the video
                        out.write(image)

            # Reached end of the file, exit the loop
            elif line == "FD":
                break

            # Core layer processing (we are between FB and FC)
            elif in_layer:
                # Split the data triplet in the line
                parts = line.split(',')
                if len(parts) == 3:  # segment data line
                    row, segment_length, laser_on = map(int, parts)

                    # If this is a new Y row
                    if row != last_row:
                        # Check if the previous Y segment was too short
                        if segment_end < X:
                            print(f"\nError in layer {current_layer}: row {row} is too short. Laser X gets up to {segment_end}")
                            error_flag = True
                            if visuals:
                                draw_segment(current_layer, image, last_row, segment_start, X, c_red)
                        # Reset parameters for the new line
                        segment_start = 0
                    
                    # X coordinate end of the segment to draw
                    segment_end = segment_start + segment_length

                    if segment_end > X:
                        # Segment exceeds X maximum value?
                        print(f"\nError in layer {current_layer}: row {row} exceeds limits. Laser X gets up to {segment_end}")
                        error_flag = True
                        if visuals:
                            draw_segment(current_layer, image, row, segment_start, X, c_red)
                    else:
                        # Draw the line if the laser is on
                        if visuals and laser_on == 1:
                            draw_segment(current_layer, image, row, segment_start, segment_end, c_white)

                    last_row = row 
                    segment_start = segment_end

        # We reached the end of the analysis, so we clean up the progress bar
        if '|' in line:
            # In case we reached the actual end of the file
            print(f'\r[{bar}] {current_layer}', end=' ')
            vlog(f"Processing layer {current_layer}")
        else:
            vlog(f"Processing layer {current_layer-1}")

        # Report is there were errors in the file
        if len(error_layers) > 0:
            print("!!! Errors in the following layers:", end=" ")
            print(*error_layers)
        else:
            vlog("No errors found in the layers")

        # In case we reached the actual end of the file, let's process also the last line with the total number of layers
        if '|' in line:
            recap = line.split('|')
            if len(recap) == 2:
                total_layers_reported = int(recap[0])
                vlog("Validating recap section...")
                if layer_count == total_layers_reported:
                    vlog(f"Recap is compliant: found {layer_count} layers, expected {total_layers_reported}.")
                else:
                    vlog(f"Recap compliance failed: found {layer_count} layers, expected {total_layers_reported}.")

        # Wrap up
        if do_video:
            out.release()
            vlog(f"Video {dir_path}.mp4 released")
        if do_pictures:
            vlog(f"Pictures available in the {dir_path} folder")

if __name__ == "__main__":

    # Start the analysis
    vlog(f"Start analisys")
    validate_file_structure(*read_parameters(sys.argv))
    vlog("Finished")
