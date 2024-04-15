import sys
import shutil
import time
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

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

max_frames = 50*400
# Record the start time
start_time = time.time()

LH, X, Y = 50, 4000, 8000                               # Expected values for Galaxy 1
expected_header = f"JieHe,{LH},{X},{Y},2,030,0,FA"      # Galaxy 1

def vlog(msg):
  #Prints timestamp and text
  print(f"{datetime.fromtimestamp(time.time()-start_time).strftime('%H:%M:%S')} - {msg}")

def create_video_from_images(image_dir, video_path, fps=24):
  """Creates a video from a directory of images.
     REQUIRES FFMPEG (winget install winget)
  """
  vlog(f"Start video creation: {video_path}")

  image_pattern = os.path.join(image_dir, "layer%d.png")  # Pattern with padding
  command = f"ffmpeg -framerate {fps} -i {image_pattern} -c:v libx264 {video_path}"
  vlog(command)
  os.system(command)

  vlog(f"Video created successfully: {video_path}")


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

            # Check if the directory exists
            if os.path.exists(dir_path):
                # Remove all contents of the directory
                shutil.rmtree(dir_path)
            
            # Create the directory
            os.makedirs(dir_path, exist_ok=True)

            if max_frames > 0:
                vlog("Initialize the frame buffer")
                # Create an empty (black) image
                img = Image.new('RGB', (Y, X), 'black')
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype('arial.ttf', 200)
                # Initialize an empty list to hold each frame as a video clip
                video_clips = []

            layer_count = 0
            current_layer = 0
            in_image = False
            
            for line in file:
                line = line.strip()

                if line.isdigit():
                    current_layer = int(line)
                    if current_layer == max_frames:
                        break
                    layer_count += 1
                    if layer_count != current_layer:
                        vlog(f"Error in layer {current_layer}: layer number doesn't match the sequence {layer_count}")
                    last_displacement = 0
                    vlog(f"Processing layer {current_layer}...")
                
                elif line == "FB":
                    last_row = 0
                    last_displacement = 0

                    if current_layer < max_frames:
                        # Clear the frame (fill it with black)
                        draw.rectangle([(0, 0), (Y, X)], fill='black')

                    # Start the analysis of the layer image data between "FB" and "FC"
                    in_image = True
                
                elif line == "FC":
                    in_image = False

                    if current_layer < max_frames:
                        # Save the temporary clip frame to file - to be optimized
                        draw.text((5, 5), f"{current_layer + 1}", fill="white", font=font)
                        temp_image_path = f"{dir_path}\\layer{current_layer}.png"
                        img.save(temp_image_path)
 
                elif line == "FD":
                    break  # Recap section starts, stop processing

                else:
                    # Data line processing
                    parts = line.split(',')
                    if len(parts) == 3 and in_image:  # Row data line
                        row, displacement, laser_on = map(int, parts)

                        if current_layer < max_frames and in_image:
                            # Draw the actual line on the clip frame, red if there is an error
                            if row != last_row:
                                last_displacement = 0
                            rd_to = last_displacement + displacement

                            if rd_to <= X:
                                to_fill = "white"
                            else:
                                vlog(f"Error in layer {current_layer}: row {row} exceeds limits. Laser X gets up to {rd_to}")
                                to_fill = "red"
                                rd_to = X
                                laser_on = 1
                            if laser_on == 1:
                                if current_layer %2 == 1:
                                    draw.line((row, last_displacement, row, rd_to), fill=to_fill)
                                else:
                                    draw.line((Y - row, last_displacement, Y - row, rd_to), fill=to_fill)
                            last_row = row 
                            last_displacement = rd_to

            # Validate recap section, reading the last line of the file
            recap = file.readline().strip().split('|')
            if len(parts) == 2:
                total_layers_reported = int(recap[0])
                vlog("Validating recap section...")
                if layer_count == total_layers_reported:
                    vlog(f"Recap is compliant: found {layer_count} layers, expected {total_layers_reported}.")
                else:
                    vlog(f"Recap compliance failed: found {layer_count} layers, expected {total_layers_reported}.")

            if max_frames > 0:
                create_video_from_images(dir_path, f"{dir_path}.mp4")
                """
                vlog("Clean up...")
                if os.path.exists(dir_path):
                    # Remove all contents of the directory
                    shutil.rmtree(dir_path)
                """

    except FileNotFoundError:
        vlog(f"Error: The file '{filename}' was not found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)

    vlog("Start...")
    filename = sys.argv[1]
    dir_path = Path(filename).stem 
    validate_file_structure(filename)
    vlog("Finished")
