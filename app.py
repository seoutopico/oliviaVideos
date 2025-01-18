import requests
from flask import Flask, request, jsonify
from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip
from PIL import Image

# Configurar la aplicación Flask
app = Flask(__name__)

# Función para crear el video
def crear_video(audio_url, image_url, bg_url, output_path="video_final.mp4"):
    # Descargar audio
    audio_response = requests.get(audio_url)
    with open("audio.mp3", "wb") as audio_file:
        audio_file.write(audio_response.content)
    audio = AudioFileClip("audio.mp3")
    
    # Descargar imagen central
    image_response = requests.get(image_url)
    with open("image.png", "wb") as image_file:
        image_file.write(image_response.content)
    image = Image.open("image.png")

    # Descargar fondo
    bg_response = requests.get(bg_url)
    with open("background.png", "wb") as bg_file:
        bg_file.write(bg_response.content)
    bg = Image.open("background.png")

    # Crear lienzo del video (1080x1080)
    video_width, video_height = 1080, 1080

    # Asegurarse de que el fondo tenga el tamaño adecuado
    bg = bg.resize((video_width, video_height), Image.ANTIALIAS)
    bg.save("resized_background.png")

    # Crear clip del fondo
    bg_clip = ImageClip("resized_background.png").set_duration(audio.duration)

    # Redimensionar imagen central si es necesario
    image_width, image_height = image.size
    max_width, max_height = 800, 800  # Tamaño máximo de la imagen central
    if image_width > max_width or image_height > max_height:
        image.thumbnail((max_width, max_height), Image.ANTIALIAS)
    image.save("resized_image.png")

    # Crear clip de la imagen central
    image_clip = ImageClip("resized_image.png").set_duration(audio.duration)
    image_clip = image_clip.set_position("center")

    # Componer el video con el fondo y la imagen
    video = CompositeVideoClip([bg_clip, image_clip]).set_audio(audio)
    video.fps = 30  # Fotogramas por segundo

    # Exportar video final
    video.write_videofile(output_path, codec="libx264", audio_codec="aac")
    return output_path


# Endpoint para recibir datos desde Make.com
@app.route('/crear-video', methods=['POST'])
def recibir_datos():
    try:
        # Leer datos JSON enviados desde Make.com
        data = request.json
        audio_url = data.get("audio_url")
        image_url = data.get("image_url")
        bg_url = data.get("bg_url")

        if not audio_url or not image_url or not bg_url:
            return jsonify({"error": "Faltan parámetros en el JSON"}), 400

        # Crear el video
        video_path = crear_video(audio_url, image_url, bg_url)

        # Responder con la ruta del video generado
        return jsonify({"message": "Video generado con éxito", "video_path": video_path})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Iniciar servidor Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
