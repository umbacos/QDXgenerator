from PIL import Image, ImageDraw
from moviepy.editor import concatenate_videoclips, ImageClip

# Create an empty (black) image
width, height = 1920, 1080
img = Image.new('RGB', (width, height), 'black')
draw = ImageDraw.Draw(img)

# Initialize an empty list to hold each frame as a video clip
video_clips = []

# Perform steps 2 to 4, ten times
for i in range(10):
    # Clear the image (fill it with black)
    draw.rectangle([(0, 0), (width, height)], fill='black')
    
    # Paint a white line on it
    start_position = (0, i * (height // 10))
    end_position = (width, i * (height // 10))
    draw.line([start_position, end_position], fill='white', width=10)
    
    # Save the image to a temporary file
    temp_image_path = f'temp_frame_{i}.png'
    img.save(temp_image_path)
    
    # Create a video clip from the image with a duration of 0.2 seconds
    clip = ImageClip(temp_image_path).set_duration(0.2)
    
    # Append the clip to the list of video clips
    video_clips.append(clip)

# Concatenate all video clips into one video
final_clip = concatenate_videoclips(video_clips, method='compose')

# Save the final video
final_clip.write_videofile("render.mp4", fps=24)

# Clean up temporary image files
for i in range(10):
    temp_image_path = f'temp_frame_{i}.png'
    try:
        os.remove(temp_image_path)
    except OSError:
        pass