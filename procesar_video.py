# procesar_video.py
# Script ejecutable para procesar un video de saque de tenis.
# Detecta la pose, guarda los keypoints en JSON y genera el video con esqueleto.
#
# Uso (con el entorno virtual activo):
#   python procesar_video.py videos/prueba/pros/video_pro.mp4
#   python procesar_video.py videos/prueba/propios/IMG_5612_horizontal.mp4

import sys
from pathlib import Path

# Importar el módulo de extracción que acabamos de crear
from src.deteccion.extractor import procesar_video

# Ruta fija al modelo de MediaPipe (descargado en modelos/)
RUTA_MODELO = Path("modelos/pose_landmarker_full.task")


def main():
    # Verificar que se pasó un argumento con la ruta del video
    if len(sys.argv) < 2:
        print("Uso: python procesar_video.py <ruta_del_video>")
        print()
        print("Ejemplos:")
        print("  python procesar_video.py videos/prueba/pros/video_pro.mp4")
        print("  python procesar_video.py videos/prueba/propios/IMG_5612_horizontal.mp4")
        sys.exit(1)

    ruta_video = Path(sys.argv[1])

    # Verificar que el archivo de video existe
    if not ruta_video.exists():
        print(f"Error: no se encontro el video en '{ruta_video}'")
        print("Verifica que la ruta sea correcta y que el archivo exista.")
        sys.exit(1)

    # Verificar que el modelo de MediaPipe está descargado
    if not RUTA_MODELO.exists():
        print(f"Error: no se encontro el modelo en '{RUTA_MODELO}'")
        print("El modelo debe estar en modelos/pose_landmarker_full.task")
        sys.exit(1)

    # Procesar el video
    procesar_video(ruta_video, RUTA_MODELO)


if __name__ == "__main__":
    main()
