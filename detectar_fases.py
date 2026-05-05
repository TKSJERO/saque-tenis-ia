"""
detectar_fases.py — Script principal del Hito 2.

Uso:
    python detectar_fases.py <ruta_json_keypoints> [ruta_video_opcional]

Ejemplos:
    python detectar_fases.py datos/keypoints/video_pro_keypoints.json
    python detectar_fases.py datos/keypoints/video_pro_keypoints.json videos/prueba/pros/video_pro.mp4

El script:
  1. Lee el JSON de keypoints generado por el Hito 1
  2. Detecta las 8 fases del saque
  3. Guarda el resultado en datos/resultados/{video}_fases.json
  4. Genera un video con las fases etiquetadas en videos/salida/{video}_fases.mp4
  5. Si el video es video_pro, imprime el reporte de validación contra ground truth
"""

import sys
import json
from pathlib import Path

# Raíz del proyecto (la carpeta que contiene este script)
RAIZ = Path(__file__).parent

# Añadir la raíz al path de Python para importar módulos de src/
sys.path.insert(0, str(RAIZ))

from src.fases.detector_fases import detectar_fases, guardar_resultado, ETIQUETAS_FASES
from src.fases.visualizador_fases import generar_video_fases


# ─────────────────────────────────────────────
# GROUND TRUTH — video_pro.mp4
# Anotación manual de Pablo (docs/ground_truth_video_pro.md)
# Tolerancia aceptada: ±15 frames (±0.5 segundos a 30 fps)
# ─────────────────────────────────────────────
GROUND_TRUTH_VIDEO_PRO = {
    "start":        5,     # revisado frame a frame: 0.17s
    "release":      156,   # revisado frame a frame: 5.2s
    "cocking":      287,   # revisado frame a frame: 9.57s
    "acceleration": 345,   # revisado frame a frame: 11.5s
    "contact":      372,   # revisado frame a frame: 12.4s (coincide con mínimo de muneca_der_y)
    "finish":       394,   # revisado frame a frame: 13.13s
    # "loading" y "deceleration" no tienen ground truth explícito
}
TOLERANCIA_FRAMES = 15


def buscar_video(nombre_video):
    """
    Busca recursivamente el archivo de video en la carpeta videos/ del proyecto.
    Devuelve la ruta si lo encuentra, None si no.
    """
    carpeta_videos = RAIZ / "videos"
    if not carpeta_videos.exists():
        return None
    for ruta in carpeta_videos.rglob(nombre_video):
        return ruta
    return None


def imprimir_reporte_validacion(fases, fps=30.0):
    """
    Compara los frames detectados contra el ground truth de video_pro.
    Imprime cuántos frames de error hay por fase y si pasan el umbral de ±15 frames.
    """
    print("\n" + "=" * 60)
    print("VALIDACIÓN CONTRA GROUND TRUTH (video_pro)")
    print(f"Tolerancia: ±{TOLERANCIA_FRAMES} frames (±{TOLERANCIA_FRAMES/fps:.2f}s)")
    print("=" * 60)

    aprobadas = 0
    total_validadas = 0

    for fase, frame_gt in GROUND_TRUTH_VIDEO_PRO.items():
        if fase not in fases:
            print(f"  {fase:15s} — no detectada (no está en el resultado)")
            continue

        frame_detectado = fases[fase]
        error = frame_detectado - frame_gt
        error_abs = abs(error)
        pasa = error_abs <= TOLERANCIA_FRAMES
        simbolo = "OK" if pasa else "FALLO"
        signo = "+" if error >= 0 else ""

        etiqueta = ETIQUETAS_FASES.get(fase, fase)
        print(
            f"  {etiqueta:20s}  GT: {frame_gt:4d}  |  "
            f"Detectado: {frame_detectado:4d}  |  "
            f"Error: {signo}{error:3d} frames  [{simbolo}]"
        )
        total_validadas += 1
        if pasa:
            aprobadas += 1

    print("-" * 60)
    print(f"Resultado: {aprobadas}/{total_validadas} fases dentro de ±{TOLERANCIA_FRAMES} frames")
    if aprobadas == total_validadas:
        print("¡Todas las fases detectadas correctamente!")
    else:
        print("Algunas fases están fuera del rango — revisar umbrales en detector_fases.py")
    print("=" * 60 + "\n")


def main():
    # ── 1. Leer argumentos ────────────────────────────────────────────────
    if len(sys.argv) < 2:
        print("Uso: python detectar_fases.py <ruta_json_keypoints> [ruta_video]")
        print("Ejemplo: python detectar_fases.py datos/keypoints/video_pro_keypoints.json")
        sys.exit(1)

    ruta_json = Path(sys.argv[1])
    if not ruta_json.exists():
        print(f"Error: no se encontró el archivo JSON: {ruta_json}")
        sys.exit(1)

    # ── 2. Detectar fases ─────────────────────────────────────────────────
    fases = detectar_fases(str(ruta_json))

    # ── 3. Guardar resultado JSON ─────────────────────────────────────────
    ruta_resultados = RAIZ / "datos" / "resultados"
    guardar_resultado(fases, str(ruta_json), str(ruta_resultados))

    # ── 4. Buscar video original ──────────────────────────────────────────
    ruta_video = None

    if len(sys.argv) >= 3:
        # El usuario pasó la ruta del video como segundo argumento
        ruta_video = Path(sys.argv[2])
        if not ruta_video.exists():
            print(f"Advertencia: no se encontró el video en la ruta indicada: {ruta_video}")
            ruta_video = None

    if ruta_video is None:
        # Intentar encontrar el video automáticamente a partir del campo "video" del JSON
        with open(ruta_json, "r", encoding="utf-8") as f:
            datos = json.load(f)
        nombre_video = datos.get("video", "")
        ruta_video = buscar_video(nombre_video)

        if ruta_video is None:
            print(f"\nNo se encontró el video '{nombre_video}' en la carpeta videos/.")
            print("Pasá la ruta manualmente como segundo argumento:")
            print(f"  python detectar_fases.py {ruta_json} <ruta_al_video>")
            print("\nEl JSON de fases se guardó correctamente. Solo falta el video.\n")
            sys.exit(0)

    print(f"Video encontrado: {ruta_video}")

    # ── 5. Generar video con etiquetas ────────────────────────────────────
    ruta_salida_videos = RAIZ / "videos" / "salida"
    generar_video_fases(
        ruta_video_entrada=str(ruta_video),
        fases=fases,
        ruta_salida_carpeta=str(ruta_salida_videos)
    )

    # ── 6. Validación contra ground truth (solo video_pro) ────────────────
    nombre_json = ruta_json.stem  # e.g. "video_pro_keypoints"
    if "video_pro" in nombre_json.lower():
        with open(ruta_json, "r", encoding="utf-8") as f:
            datos = json.load(f)
        fps = datos.get("fps", 30.0)
        imprimir_reporte_validacion(fases, fps=fps)


if __name__ == "__main__":
    main()
