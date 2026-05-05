# src/interfaz/pipeline.py
# Orquestación del pipeline completo de análisis de saque.
# Cada paso verifica si el JSON de salida ya existe en disco antes de ejecutar.
# Si existe → retorna la ruta y fue_cacheado=True sin reprocesar.

import json
import sys
from pathlib import Path

# Raíz del proyecto (tres niveles arriba de src/interfaz/pipeline.py)
RAIZ = Path(__file__).resolve().parent.parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.deteccion.extractor import procesar_video as _procesar_video
from src.fases.detector_fases import detectar_fases as _detectar_fases, guardar_resultado
from src.fases.visualizador_fases import generar_video_fases
from src.angulos.calculador_angulos import calcular_todos_los_angulos
from src.feedback.generador_feedback import (
    cargar_datos_angulos,
    construir_input_para_claude,
    generar_feedback as _generar_feedback,
    guardar_feedback,
)

RUTA_MODELO = RAIZ / "modelos" / "pose_landmarker_full.task"


def ejecutar_paso_1(ruta_video: Path, nombre_base: str):
    """
    Detecta pose con MediaPipe frame a frame.
    Si el JSON de keypoints ya existe en disco, lo reutiliza sin reprocesar.

    Retorna: (ruta_keypoints, ruta_esqueleto, fue_cacheado, total_frames, frames_con_pose)
    """
    ruta_keypoints = RAIZ / "datos" / "keypoints" / f"{nombre_base}_keypoints.json"
    ruta_esqueleto = RAIZ / "videos"  / "salida"   / f"{nombre_base}_esqueleto.mp4"

    if ruta_keypoints.exists():
        with open(ruta_keypoints, encoding="utf-8") as f:
            datos = json.load(f)
        total_frames    = datos.get("total_frames", 0)
        frames_con_pose = sum(1 for fr in datos["frames"] if fr["pose_detectada"])
        return ruta_keypoints, ruta_esqueleto, True, total_frames, frames_con_pose

    # Crear carpetas si no existen
    ruta_keypoints.parent.mkdir(parents=True, exist_ok=True)
    ruta_esqueleto.parent.mkdir(parents=True, exist_ok=True)

    try:
        ruta_json_out, ruta_video_out = _procesar_video(ruta_video, RUTA_MODELO)
    except FileNotFoundError:
        raise RuntimeError(
            "No se pudo abrir el video. Verificá que el archivo no esté dañado."
        )
    except Exception as e:
        raise RuntimeError(
            f"Error al detectar pose con MediaPipe: {type(e).__name__} — {e}"
        )

    with open(ruta_json_out, encoding="utf-8") as f:
        datos = json.load(f)
    total_frames    = datos.get("total_frames", 0)
    frames_con_pose = sum(1 for fr in datos["frames"] if fr["pose_detectada"])

    if total_frames > 0 and (frames_con_pose / total_frames) < 0.10:
        raise RuntimeError(
            f"MediaPipe detectó pose en muy pocos frames "
            f"({frames_con_pose}/{total_frames}). "
            "Asegurate de que el jugador sea visible de cuerpo completo "
            "y que el video sea horizontal."
        )

    return Path(ruta_json_out), Path(ruta_video_out), False, total_frames, frames_con_pose


def ejecutar_paso_2(ruta_keypoints: Path, ruta_video_original: Path, nombre_base: str):
    """
    Detecta las fases del saque y genera el video con etiquetas de fase.
    Si el JSON de fases ya existe en disco, lo reutiliza sin reprocesar.

    Retorna: (ruta_fases, ruta_video_fases, fue_cacheado, n_fases)
    """
    ruta_fases       = RAIZ / "datos"   / "resultados" / f"{nombre_base}_fases.json"
    ruta_video_fases = RAIZ / "videos"  / "salida"     / f"{nombre_base}_fases.mp4"

    if ruta_fases.exists():
        with open(ruta_fases, encoding="utf-8") as f:
            datos = json.load(f)
        n_fases = len(datos.get("fases", {}))
        return ruta_fases, ruta_video_fases, True, n_fases

    ruta_fases.parent.mkdir(parents=True, exist_ok=True)
    ruta_video_fases.parent.mkdir(parents=True, exist_ok=True)

    try:
        fases = _detectar_fases(str(ruta_keypoints))
    except Exception as e:
        raise RuntimeError(f"Error al detectar fases del saque: {e}")

    guardar_resultado(fases, str(ruta_keypoints), str(ruta_fases.parent))

    try:
        # generar_video_fases recibe el dict plano {"start": frame, ...}
        generar_video_fases(
            ruta_video_entrada=str(ruta_video_original),
            fases=fases,
            ruta_salida_carpeta=str(ruta_video_fases.parent),
        )
    except Exception:
        # El video de fases es opcional — si falla, el análisis continúa igual
        pass

    return ruta_fases, ruta_video_fases, False, len(fases)


def ejecutar_paso_3(ruta_keypoints: Path, ruta_fases: Path, nombre_base: str):
    """
    Calcula los ángulos articulares biomecánicos por fase.
    Si el JSON de ángulos ya existe en disco, lo reutiliza sin reprocesar.

    Retorna: (ruta_angulos, fue_cacheado, n_parametros)
    """
    ruta_angulos = RAIZ / "datos" / "angulos" / f"{nombre_base}_angulos.json"

    if ruta_angulos.exists():
        with open(ruta_angulos, encoding="utf-8") as f:
            datos = json.load(f)
        n_params = len(datos.get("resumen_por_fase", {}))
        return ruta_angulos, True, n_params

    ruta_angulos.parent.mkdir(parents=True, exist_ok=True)

    try:
        # calcular_todos_los_angulos recibe los dicts crudos de los JSON
        with open(ruta_keypoints, encoding="utf-8") as f:
            datos_keypoints = json.load(f)
        with open(ruta_fases, encoding="utf-8") as f:
            datos_fases = json.load(f)
        resultado = calcular_todos_los_angulos(datos_keypoints, datos_fases)
    except Exception as e:
        raise RuntimeError(f"Error al calcular ángulos articulares: {e}")

    with open(ruta_angulos, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    n_params = len(resultado.get("resumen_por_fase", {}))
    return ruta_angulos, False, n_params


def ejecutar_paso_4(ruta_angulos: Path, nombre_base: str):
    """
    Genera feedback biomecánico con la API de Claude.
    No se cachea: siempre se regenera para reflejar el estado actual del sistema.

    Retorna: (texto_feedback, metricas)
    metricas contiene: tiempo_segundos, tokens_input, tokens_output, costo_usd
    """
    ruta_feedback = RAIZ / "datos" / "feedback" / f"{nombre_base}_feedback.md"
    ruta_feedback.parent.mkdir(parents=True, exist_ok=True)

    try:
        datos              = cargar_datos_angulos(str(ruta_angulos))
        input_estructurado = construir_input_para_claude(datos)
        texto_feedback, metricas = _generar_feedback(input_estructurado)
    except Exception as e:
        mensaje = str(e).lower()
        if "authentication" in mensaje or "401" in mensaje or "api_key" in mensaje:
            raise RuntimeError(
                "API key de Anthropic inválida. "
                "Verificá que el archivo .env contiene ANTHROPIC_API_KEY=sk-ant-..."
            )
        if "connection" in mensaje or "network" in mensaje or "timeout" in mensaje:
            raise RuntimeError(
                "No se pudo conectar con la API de Claude. "
                "Verificá tu conexión a internet e intentá de nuevo."
            )
        raise RuntimeError(f"Error al generar feedback con Claude: {e}")

    guardar_feedback(texto_feedback, str(ruta_feedback))
    return texto_feedback, metricas
