import sys
import os
import shutil
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from moviepy.editor import concatenate_videoclips, ImageClip

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


# Record the start time
start_time = time.time()

LH, X, Y = 50, 4000, 8000                               # Expected values for Galaxy 1
expected_header = f"JieHe,{LH},{X},{Y},2,030,0,FA"      # Galaxy 1

def vlog(msg):
    print(f"{datetime.fromtimestamp(time.time()-start_time).strftime('%H:%M:%S')} - {msg}")

def dump_layer(filename):
    try:
        vlog("Opening and reading the file...")
        with open(filename, 'r') as file:
            first_line = file.readline()
            
            # Validate header
            vlog("Validating header...")
            header = first_line.strip()
            if header == expected_header:
                vlog(f"Header is compliant: LH={LH}, X={X}, Y={Y}")
            else:
                vlog(f"Header compliance failed: found {header}")

            # Create an empty (black) image
            img = Image.new('RGB', (Y, X), 'black')
            draw = ImageDraw.Draw(img)

            current_layer = 0
            in_image = False
            in_layer = False

            for line in file:
                line = line.strip()

                if line.isdigit():
                    current_layer = int(line)
                    if current_layer == the_layer:
                        vlog(f"Processing layer {current_layer}...")
                        in_layer = True
                
                elif line == "FB" and in_layer == True:
                    in_image = True
                    prev_row = 0
                    prev_displacement = 0;
                
                elif line == "FC" and in_image == True:
                    base, extension = os.path.splitext(filename)
                    temp_image_path = f"{base}{current_layer}.png"
                    img.save(temp_image_path)
                    break
 
                elif line == "FD":
                    vlog("Layer number not found in file")
                    break  # Recap section starts, stop processing

                elif in_image == True:
                    # Data line processing
                    parts = line.split(',')
                    if len(parts) == 3:  # Row data line
                        row, displacement, laser_on = map(int, parts)
                        if prev_row != row:
                            prev_row = row
                            prev_displacement = 0

                        rd_to = prev_displacement + displacement
                        if rd_to <= X:
                            to_fill = "white"
                        else:
                            to_fill = "red"
                            rd_to = X
                            laser_on = 1
                        if laser_on == 1:
                            if current_layer %2 == 1:
                                draw.line((row, prev_displacement, row, rd_to), fill=to_fill)
                            else:
                                draw.line((Y - row, prev_displacement, Y - row, rd_to), fill=to_fill)
                        prev_displacement = rd_to
    
    except FileNotFoundError:
        vlog(f"Error: The file '{filename}' was not found.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python dump_frame.py <filename> <layer>")
        sys.exit(1)

    vlog("Start...")
    filename = sys.argv[1]
    the_layer = int(sys.argv[2])

    dump_layer(filename)
    vlog("Finished")
