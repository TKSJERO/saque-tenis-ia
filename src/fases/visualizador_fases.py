"""
visualizador_fases.py — Genera un video con la fase del saque escrita en cada frame.

Usa los keypoints ya extraídos (JSON del Hito 1) y el dict de fases del detector.
No reprocesa con MediaPipe.
"""

import cv2
import numpy as np
from pathlib import Path

from src.fases.detector_fases import ETIQUETAS_FASES, asignar_fase_por_frame


# Colores BGR de OpenCV
BLANCO    = (255, 255, 255)
NEGRO     = (0, 0, 0)
AMARILLO  = (0, 255, 255)   # para el rectángulo de transición


def _dibujar_texto_con_borde(frame, texto, pos, escala, grosor_texto, grosor_borde):
    """
    Escribe texto en blanco con borde negro para que sea legible sobre
    cualquier fondo de video.
    Dibuja primero el borde (en negro, más grueso) y encima el texto (en blanco).
    """
    fuente = cv2.FONT_HERSHEY_DUPLEX
    # Borde negro
    cv2.putText(frame, texto, pos, fuente, escala, NEGRO,
                grosor_borde, cv2.LINE_AA)
    # Texto blanco encima
    cv2.putText(frame, texto, pos, fuente, escala, BLANCO,
                grosor_texto, cv2.LINE_AA)


def generar_video_fases(ruta_video_entrada, fases, ruta_salida_carpeta, fps_original=30.0):
    """
    Lee el video original y escribe un video nuevo con:
      - Nombre de la fase en la esquina superior izquierda (grande y legible)
      - Línea secundaria con número de frame y timestamp en segundos
      - Rectángulo amarillo en el borde superior durante los 5 frames de cada
        transición de fase

    Args:
        ruta_video_entrada:   ruta al video original (.mp4 o .mov)
        fases:                dict {"start": frame, "release": frame, ...}
        ruta_salida_carpeta:  carpeta donde guardar el video de salida
        fps_original:         FPS del video (se lee del video si es posible)

    Returns:
        ruta del video de salida como string
    """
    ruta_video_entrada = Path(ruta_video_entrada)
    ruta_salida_carpeta = Path(ruta_salida_carpeta)
    ruta_salida_carpeta.mkdir(parents=True, exist_ok=True)

    nombre_salida = ruta_video_entrada.stem + "_fases.mp4"
    ruta_salida = ruta_salida_carpeta / nombre_salida

    # Abrir video de entrada
    cap = cv2.VideoCapture(str(ruta_video_entrada))
    if not cap.isOpened():
        raise FileNotFoundError(f"No se pudo abrir el video: {ruta_video_entrada}")

    ancho  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS) or fps_original
    total  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"\nGenerando video de fases:")
    print(f"  Entrada : {ruta_video_entrada}")
    print(f"  Salida  : {ruta_salida}")
    print(f"  Tamaño  : {ancho}x{alto} | FPS: {fps} | Frames: {total}")

    # VideoWriter con codec mp4v
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(ruta_salida), fourcc, fps, (ancho, alto))

    # Asignar etiqueta de fase a cada frame
    etiquetas_por_frame = asignar_fase_por_frame(fases, total)

    # Conjunto de frames de transición (inicio de cada fase ± 5 frames)
    frames_transicion = set()
    for frame_inicio in fases.values():
        for f in range(frame_inicio, min(frame_inicio + 5, total)):
            frames_transicion.add(f)

    # ── Parámetros de texto proporcionales al alto del video ──────────────
    # Escala principal: aproximadamente alto/15 píxeles de alto de fuente.
    # cv2.FONT_HERSHEY_DUPLEX a escala 1.0 ≈ 20px → escala = (alto/15) / 20
    escala_principal = (alto / 15) / 20
    escala_secundaria = escala_principal * 0.45

    grosor_texto    = max(1, int(escala_principal * 2))
    grosor_borde    = grosor_texto + 2

    # Margen desde el borde izquierdo/superior
    margen_x = int(alto * 0.02)
    margen_y = int(alto * 0.08)

    # Alto del rectángulo de transición
    alto_rect_transicion = max(8, alto // 25)

    # ── Procesar frames ───────────────────────────────────────────────────
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        fase_actual = etiquetas_por_frame[frame_idx] if frame_idx < len(etiquetas_por_frame) else "pre_start"
        etiqueta = ETIQUETAS_FASES.get(fase_actual, fase_actual)
        tiempo_seg = frame_idx / fps

        # Rectángulo amarillo en transición de fase
        if frame_idx in frames_transicion:
            cv2.rectangle(
                frame,
                (0, 0),
                (ancho, alto_rect_transicion),
                AMARILLO,
                thickness=-1  # relleno
            )

        # Línea 1: nombre de la fase (grande)
        _dibujar_texto_con_borde(
            frame, etiqueta,
            pos=(margen_x, margen_y),
            escala=escala_principal,
            grosor_texto=grosor_texto,
            grosor_borde=grosor_borde
        )

        # Línea 2: frame y timestamp (más pequeño, debajo de la línea 1)
        texto_info = f"Frame: {frame_idx} / {total}  |  Tiempo: {tiempo_seg:.2f}s"
        pos_linea2 = (margen_x, margen_y + int(alto / 12))
        _dibujar_texto_con_borde(
            frame, texto_info,
            pos=pos_linea2,
            escala=escala_secundaria,
            grosor_texto=max(1, grosor_texto - 1),
            grosor_borde=max(2, grosor_borde - 1)
        )

        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()

    print(f"  Video generado con {frame_idx} frames.\n")
    return str(ruta_salida)
