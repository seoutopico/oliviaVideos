# app.py
from flask import Flask, request, jsonify, send_file
from moviepy.editor import VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip
import requests
import os
from io import BytesIO
from PIL import Image
import tempfile

app = Flask(__name__)

def download_file(url):
    response = requests.get(url)
    response.raise_for_status()
    return BytesIO(response.content)

@app.route('/create-video', methods=['POST'])
def create_video():
    try:
        data = request.json
        audio_url = data['audio_url']
        image_url = data['image_url']
        bg_url = data['bg_url']

        # Create temporary directory for files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download and save audio
            audio_data = download_file(audio_url)
            audio_path = os.path.join(temp_dir, 'audio.mp3')
            with open(audio_path, 'wb') as f:
                f.write(audio_data.getvalue())
            
            # Download and process image
            image_data = download_file(image_url)
            image = Image.open(image_data)
            image_path = os.path.join(temp_dir, 'image.png')
            image.save(image_path)
            
            # Download and process background
            bg_data = download_file(bg_url)
            bg = Image.open(bg_data)
            bg_path = os.path.join(temp_dir, 'bg.png')
            bg.save(bg_path)
            
            # Create video
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # Create background clip
            bg_clip = ImageClip(bg_path).set_duration(duration).resize((1080, 1080))
            
            # Create foreground image clip
            img_clip = ImageClip(image_path).set_duration(duration)
            
            # Resize and center the image if needed (maintaining aspect ratio)
            # Adjust the width to be 70% of the canvas
            target_width = int(1080 * 0.7)
            img_clip = img_clip.resize(width=target_width)
            img_clip = img_clip.set_position('center')
            
            # Combine clips
            final_clip = CompositeVideoClip([bg_clip, img_clip])
            final_clip = final_clip.set_audio(audio_clip)
            
            # Export video
            output_path = os.path.join(temp_dir, 'output.mp4')
            final_clip.write_videofile(output_path, 
                                     fps=24, 
                                     codec='libx264', 
                                     audio_codec='aac')
            
            # Return the video file
            return send_file(output_path, 
                           mimetype='video/mp4',
                           as_attachment=True,
                           download_name='output.mp4')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv('PORT', 8080))
