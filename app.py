from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import tempfile
import os
import requests
from moviepy.editor import AudioFileClip, ImageClip
from PIL import Image
import numpy as np
import aiofiles
import uvicorn

app = FastAPI()

class VideoRequest(BaseModel):
    image_url: str
    audio_url: str

def download_file(url: str, temp_path: str):
    """Descarga un archivo desde una URL"""
    response = requests.get(url)
    response.raise_for_status()
    with open(temp_path, 'wb') as f:
        f.write(response.content)

def process_image(image_path):
    """Procesa la imagen con Pillow moderno"""
    with Image.open(image_path) as img:
        img_resized = img.resize((1080, 1080), Image.Resampling.LANCZOS)
        return np.array(img_resized)

def create_simple_video(image_path, audio_path):
    """Crea un video simple: una imagen + audio"""
    try:
        # Procesar imagen con Pillow
        img_array = process_image(image_path)
        video = ImageClip(img_array)
        
        # Agregar audio
        audio = AudioFileClip(audio_path)
        final_video = video.set_audio(audio).set_duration(audio.duration)
        
        # Guardar video
        output_path = tempfile.mktemp('.mp4')
        final_video.write_videofile(
            output_path,
            fps=1,
            codec='libx264',
            preset='ultrafast',
            audio_codec='aac',
            threads=4,
            logger=None  # Desactivar logs
        )
        
        # Limpiar recursos
        audio.close()
        video.close()
        final_video.close()
        
        return output_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating video: {str(e)}")

@app.post("/create-video")
async def create_video(request: VideoRequest):
    try:
        # Crear directorio temporal
        temp_dir = tempfile.mkdtemp()
        
        # Rutas temporales para los archivos
        image_path = os.path.join(temp_dir, "image.jpg")
        audio_path = os.path.join(temp_dir, "audio.mp3")
        
        # Descargar archivos
        download_file(request.image_url, image_path)
        download_file(request.audio_url, audio_path)
        
        # Crear video
        output_path = create_simple_video(image_path, audio_path)
        
        # Leer el video y devolverlo
        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename="video.mp4",
            background=None  # Para permitir que FastAPI maneje el cierre
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Limpiar archivos temporales
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)
            if 'output_path' in locals() and os.path.exists(output_path):
                os.remove(output_path)
            os.rmdir(temp_dir)
        except:
            pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
