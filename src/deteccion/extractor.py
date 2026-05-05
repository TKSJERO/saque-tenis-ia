# src/deteccion/extractor.py
# Módulo principal de extracción de keypoints.
# Toma un video mp4/mov, detecta los 33 puntos del cuerpo en cada frame
# usando MediaPipe Pose Landmarker, guarda los datos en JSON y genera
# un video de salida con el esqueleto dibujado encima.

import cv2
import json
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.vision import RunningMode
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# NOMBRES DE LOS 33 PUNTOS DE MEDIAPIPE POSE
# MediaPipe detecta exactamente 33 puntos del cuerpo, numerados del 0 al 32.
# Esta lista los nombra en orden para que el JSON sea legible.
# ─────────────────────────────────────────────────────────────────────────────
NOMBRES_LANDMARKS = [
    "nariz",
    "ojo_izq_interno", "ojo_izq", "ojo_izq_externo",
    "ojo_der_interno", "ojo_der", "ojo_der_externo",
    "oreja_izq", "oreja_der",
    "boca_izq", "boca_der",
    "hombro_izq", "hombro_der",
    "codo_izq", "codo_der",
    "muneca_izq", "muneca_der",
    "pulgar_izq", "pulgar_der",
    "indice_izq", "indice_der",
    "menique_izq", "menique_der",
    "cadera_izq", "cadera_der",
    "rodilla_izq", "rodilla_der",
    "tobillo_izq", "tobillo_der",
    "talon_izq", "talon_der",
    "pie_izq", "pie_der",
]

# ─────────────────────────────────────────────────────────────────────────────
# CONEXIONES ENTRE PUNTOS PARA DIBUJAR EL ESQUELETO
# Cada par (a, b) representa una línea entre el punto a y el punto b.
# Los números son los índices de NOMBRES_LANDMARKS arriba.
# ─────────────────────────────────────────────────────────────────────────────
CONEXIONES = [
    # Cara
    (0, 1), (1, 2), (2, 3), (3, 7),
    (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10),
    # Tronco
    (11, 12), (11, 23), (12, 24), (23, 24),
    # Brazo izquierdo
    (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    # Brazo derecho
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    # Pierna izquierda
    (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),
    # Pierna derecha
    (24, 26), (26, 28), (28, 30), (28, 32), (30, 32),
]


def _dibujar_esqueleto(frame, landmarks, ancho, alto):
    """
    Dibuja el esqueleto sobre un frame de video.
    Recibe los landmarks detectados y los convierte de coordenadas
    normalizadas (0.0 a 1.0) a píxeles reales según el tamaño del frame.
    """
    # Convertir cada landmark de coordenadas relativas a píxeles absolutos
    puntos = []
    for lm in landmarks:
        px = int(lm.x * ancho)
        py = int(lm.y * alto)
        puntos.append((px, py))

    # Dibujar líneas entre los puntos conectados (color verde, grosor 2px)
    for a, b in CONEXIONES:
        if a < len(puntos) and b < len(puntos):
            cv2.line(frame, puntos[a], puntos[b], (0, 255, 0), 2)

    # Dibujar un círculo en cada punto del cuerpo (color rojo, relleno)
    for px, py in puntos:
        cv2.circle(frame, (px, py), 4, (0, 0, 255), -1)

    return frame


def procesar_video(ruta_video, ruta_modelo):
    """
    Procesa un video completo: detecta pose en cada frame, guarda los
    keypoints en un JSON y genera un video con el esqueleto dibujado.

    Parámetros:
        ruta_video  : ruta al archivo de video (mp4, mov, etc.)
        ruta_modelo : ruta al archivo pose_landmarker_full.task

    Retorna:
        (ruta_json, ruta_video_salida) — rutas de los archivos generados
    """
    ruta_video  = Path(ruta_video)
    ruta_modelo = Path(ruta_modelo)
    nombre_base = ruta_video.stem  # nombre del archivo sin extensión

    # Definir dónde se guardarán los archivos de salida
    ruta_json          = Path("datos/keypoints") / f"{nombre_base}_keypoints.json"
    ruta_video_salida  = Path("videos/salida")   / f"{nombre_base}_esqueleto.mp4"

    # ── Abrir el video con OpenCV ──────────────────────────────────────────
    cap = cv2.VideoCapture(str(ruta_video))
    if not cap.isOpened():
        raise FileNotFoundError(f"No se pudo abrir el video: {ruta_video}")

    fps          = cap.get(cv2.CAP_PROP_FPS)
    ancho        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto         = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"\nProcesando: {ruta_video.name}")
    print(f"  {ancho}x{alto}px  |  {fps:.0f} fps  |  {total_frames} frames")
    print(f"  Modelo: {ruta_modelo.name}")
    print()

    # ── Configurar MediaPipe PoseLandmarker en modo VIDEO ──────────────────
    # El modo VIDEO procesa frames en secuencia con timestamps crecientes.
    # Es más eficiente que IMAGE porque aprovecha la continuidad del movimiento.
    opciones = mp_vision.PoseLandmarkerOptions(
        base_options=mp_tasks.BaseOptions(model_asset_path=str(ruta_modelo)),
        running_mode=RunningMode.VIDEO,
        num_poses=1,                  # Solo hay un jugador en el video
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    # ── Configurar el video de salida ──────────────────────────────────────
    # mp4v es el codec estándar para archivos .mp4 en Windows
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(ruta_video_salida), fourcc, fps, (ancho, alto))

    # ── Procesar frame a frame ─────────────────────────────────────────────
    frames_data     = []
    frames_con_pose = 0
    frames_sin_pose = 0

    with mp_vision.PoseLandmarker.create_from_options(opciones) as detector:
        frame_num = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break  # Fin del video

            # Calcular el timestamp en milisegundos para este frame
            timestamp_ms = int(frame_num * (1000.0 / fps))

            # Convertir el frame de BGR (formato OpenCV) a RGB (formato MediaPipe)
            # OpenCV usa BGR por razones históricas; MediaPipe necesita RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image  = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

            # Detectar la pose en este frame
            resultado    = detector.detect_for_video(mp_image, timestamp_ms)
            pose_detectada = len(resultado.pose_landmarks) > 0

            if pose_detectada:
                frames_con_pose += 1
                # Extraer los 33 landmarks con sus coordenadas y visibilidad
                landmarks_data = []
                for i, lm in enumerate(resultado.pose_landmarks[0]):
                    landmarks_data.append({
                        "id":         i,
                        "nombre":     NOMBRES_LANDMARKS[i],
                        "x":          round(lm.x, 6),
                        "y":          round(lm.y, 6),
                        "z":          round(lm.z, 6),
                        "visibility": round(lm.visibility, 6),
                    })
                # Dibujar el esqueleto sobre el frame original
                frame = _dibujar_esqueleto(frame, resultado.pose_landmarks[0], ancho, alto)
            else:
                frames_sin_pose += 1
                landmarks_data  = []  # Frame sin detección: lista vacía

            # Guardar datos de este frame
            frames_data.append({
                "frame":        frame_num,
                "timestamp_ms": timestamp_ms,
                "pose_detectada": pose_detectada,
                "landmarks":    landmarks_data,
            })

            # Escribir el frame (con o sin esqueleto) al video de salida
            writer.write(frame)

            # Mostrar progreso cada 50 frames
            if frame_num % 50 == 0:
                pct = int(frame_num / total_frames * 100) if total_frames > 0 else 0
                print(f"  Frame {frame_num}/{total_frames}  ({pct}%)...", end="\r")

            frame_num += 1

    # Liberar los recursos de video
    cap.release()
    writer.release()
    print(" " * 50, end="\r")  # Limpiar la línea de progreso

    # ── Guardar el JSON de keypoints ───────────────────────────────────────
    datos_json = {
        "video":        ruta_video.name,
        "fps":          fps,
        "resolucion":   {"ancho": ancho, "alto": alto},
        "total_frames": total_frames,
        "frames":       frames_data,
    }

    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(datos_json, f, ensure_ascii=False, indent=2)

    # ── Imprimir resumen final ─────────────────────────────────────────────
    pct_ok   = (frames_con_pose / total_frames * 100) if total_frames > 0 else 0
    pct_fail = (frames_sin_pose / total_frames * 100) if total_frames > 0 else 0

    print("=" * 50)
    print(f"Video procesado : {ruta_video.name}")
    print(f"Frames totales  : {total_frames}")
    print(f"Pose detectada  : {frames_con_pose}  ({pct_ok:.1f}%)")
    print(f"Sin deteccion   : {frames_sin_pose}  ({pct_fail:.1f}%)")
    print(f"JSON guardado   : {ruta_json}")
    print(f"Video guardado  : {ruta_video_salida}")
    print("=" * 50)

    return ruta_json, ruta_video_salida
