# app.py — Analizador de Saque de Tenis
# Interfaz Streamlit que orquesta el pipeline completo de análisis biomecánico.
#
# Ejecutar con el entorno virtual activo:
#   venv\Scripts\streamlit run app.py

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Raíz del proyecto en el path (necesario para imports de src/)
RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

# Cargar .env antes de cualquier import que use la API key
load_dotenv()

import urllib.request

from src.interfaz.estilos import inyectar_css
from src.interfaz.pipeline import (
    ejecutar_paso_1,
    ejecutar_paso_2,
    ejecutar_paso_3,
    ejecutar_paso_4,
)

# ── Configuración de página ─────────────────────────────────────────────────
# Debe ser la primera llamada a Streamlit en el script.
st.set_page_config(
    page_title="Saque IA",
    page_icon="🎾",
    layout="centered",
    initial_sidebar_state="collapsed",
)
inyectar_css()


# ── Descarga automática del modelo de MediaPipe ─────────────────────────────

def descargar_modelo_si_falta():
    """Descarga el modelo de MediaPipe (~30 MB) si no está en disco."""
    ruta_modelo = RAIZ / "modelos" / "pose_landmarker_full.task"
    if ruta_modelo.exists():
        return
    url = (
        "https://storage.googleapis.com/mediapipe-models/"
        "pose_landmarker/pose_landmarker_full/float16/latest/"
        "pose_landmarker_full.task"
    )
    ruta_modelo.parent.mkdir(parents=True, exist_ok=True)
    with st.spinner("Descargando modelo de detección de pose (~30 MB)..."):
        urllib.request.urlretrieve(url, ruta_modelo)


descargar_modelo_si_falta()


# ── Verificación silenciosa de prerequisitos ────────────────────────────────

def verificar_prerequisitos():
    """
    Verifica que el modelo de MediaPipe y la API key de Anthropic estén
    disponibles antes de permitir subir un video.
    Retorna lista de strings con los errores encontrados (vacía si todo OK).
    """
    errores = []

    ruta_modelo = RAIZ / "modelos" / "pose_landmarker_full.task"
    if not ruta_modelo.exists():
        errores.append(
            "**Modelo de MediaPipe no encontrado** "
            "(`modelos/pose_landmarker_full.task`).\n\n"
            "Descargalo corriendo este comando en tu terminal con el entorno virtual activo:\n\n"
            "```\n"
            "python -c \""
            "import urllib.request; "
            "urllib.request.urlretrieve("
            "'https://storage.googleapis.com/mediapipe-models/pose_landmarker"
            "/pose_landmarker_full/float16/latest/pose_landmarker_full.task', "
            "'modelos/pose_landmarker_full.task')"
            "\"\n"
            "```"
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or not api_key.startswith("sk-ant-"):
        errores.append(
            "**API key de Anthropic no encontrada.**\n\n"
            "Verificá que el archivo `.env` existe en la raíz del proyecto "
            "y contiene exactamente esta línea:\n\n"
            "```\nANTHROPIC_API_KEY=sk-ant-...\n```"
        )

    return errores


# ── Header ──────────────────────────────────────────────────────────────────
st.markdown('<p class="app-titulo">SAQUE IA</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="app-subtitulo">Análisis biomecánico de tu saque de tenis</p>',
    unsafe_allow_html=True,
)
st.markdown('<hr class="separador">', unsafe_allow_html=True)

# Mostrar errores de prerequisitos y detener si falta algo esencial
prerequisitos_faltantes = verificar_prerequisitos()
if prerequisitos_faltantes:
    for error in prerequisitos_faltantes:
        st.error(error)
    st.stop()


# ── Inicialización de session_state ─────────────────────────────────────────

def _inicializar_estado(nombre_archivo=None):
    """
    Inicializa o reinicia todas las claves del session_state.
    Se llama al arrancar la app y cuando el usuario sube un video diferente.
    """
    st.session_state.video_nombre        = nombre_archivo
    st.session_state.video_guardado_en   = None
    st.session_state.video_es_vertical   = None
    st.session_state.confirmar_vertical  = False
    st.session_state.analisis_completado = False
    st.session_state.feedback_texto      = None
    st.session_state.feedback_metricas   = None
    st.session_state.rutas_videos        = {}

if "video_nombre" not in st.session_state:
    _inicializar_estado()


# ── Upload de video ──────────────────────────────────────────────────────────
archivo_subido = st.file_uploader(
    "Subí tu video del saque",
    type=["mp4", "mov"],
    help="Video horizontal (.mp4 o .mov). El jugador debe ser visible de cuerpo completo.",
)

# Sin video subido: no hay nada más que mostrar
if archivo_subido is None:
    st.stop()

# Si cambió el video (nombre diferente), resetear todo el estado previo
nombre_archivo = archivo_subido.name
if st.session_state.video_nombre != nombre_archivo:
    _inicializar_estado(nombre_archivo)

nombre_base        = Path(nombre_archivo).stem
ruta_video_entrada = RAIZ / "videos" / "entrada" / nombre_archivo

# Guardar el archivo en disco solo la primera vez que se sube
if st.session_state.video_guardado_en is None:
    ruta_video_entrada.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_video_entrada, "wb") as f:
        f.write(archivo_subido.read())
    st.session_state.video_guardado_en = str(ruta_video_entrada)
else:
    ruta_video_entrada = Path(st.session_state.video_guardado_en)

# Verificar orientación del video (solo la primera vez)
if st.session_state.video_es_vertical is None:
    import cv2
    cap = cv2.VideoCapture(str(ruta_video_entrada))
    if not cap.isOpened():
        st.error(
            "No se pudo leer el video. "
            "Verificá que el archivo no esté dañado y sea un .mp4 válido."
        )
        st.stop()
    ancho_video = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto_video  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    st.session_state.video_es_vertical = alto_video > ancho_video

st.caption(f"Video cargado: **{nombre_archivo}**")

# Advertencia si el video es vertical — pedir confirmación antes de continuar
if st.session_state.video_es_vertical and not st.session_state.confirmar_vertical:
    st.markdown(
        '<div class="advertencia-vertical">'
        "⚠️ <strong>Tu video está en vertical (portrait).</strong> "
        "El sistema funciona mejor con videos horizontales (landscape). "
        "Los ángulos biomecánicos pueden ser menos precisos desde esta orientación."
        "</div>",
        unsafe_allow_html=True,
    )
    col_si, col_no, _ = st.columns([1.4, 1, 2.6])
    with col_si:
        if st.button("Continuar de todas formas", type="primary"):
            st.session_state.confirmar_vertical = True
            st.rerun()
    with col_no:
        if st.button("Cancelar"):
            _inicializar_estado()
            st.rerun()
    st.stop()


# ── Botón de análisis ────────────────────────────────────────────────────────
# Solo se muestra si el análisis no está completo todavía.
if not st.session_state.analisis_completado:
    if not st.button("▶  Analizar saque", type="primary", use_container_width=True):
        st.stop()

    # ── Paso 1: Detección de pose con MediaPipe ───────────────────────────
    with st.status("Detectando pose con MediaPipe...", expanded=True) as estado_1:
        try:
            ruta_kp, ruta_esqueleto, cacheado_1, total_fr, frames_pose = ejecutar_paso_1(
                ruta_video_entrada, nombre_base
            )
        except RuntimeError as e:
            estado_1.update(label="Error en detección de pose", state="error")
            st.error(str(e))
            st.stop()

        if cacheado_1:
            estado_1.update(
                label=f"⚡ Pose detectada — resultado guardado  ({frames_pose}/{total_fr} frames)",
                state="complete",
                expanded=False,
            )
        else:
            estado_1.update(
                label=f"✓ Pose detectada — {frames_pose}/{total_fr} frames procesados",
                state="complete",
                expanded=False,
            )

    # ── Paso 2: Detección de fases del saque ─────────────────────────────
    with st.status("Identificando fases del saque...", expanded=True) as estado_2:
        try:
            ruta_fases, ruta_video_fases, cacheado_2, n_fases = ejecutar_paso_2(
                ruta_kp, ruta_video_entrada, nombre_base
            )
        except RuntimeError as e:
            estado_2.update(label="Error en detección de fases", state="error")
            st.error(str(e))
            st.stop()

        if cacheado_2:
            estado_2.update(
                label=f"⚡ Fases detectadas — resultado guardado  ({n_fases} fases)",
                state="complete",
                expanded=False,
            )
        else:
            estado_2.update(
                label=f"✓ {n_fases} fases del saque identificadas",
                state="complete",
                expanded=False,
            )

    # ── Paso 3: Cálculo de ángulos articulares ────────────────────────────
    with st.status("Calculando ángulos articulares...", expanded=True) as estado_3:
        try:
            ruta_angulos, cacheado_3, n_params = ejecutar_paso_3(
                ruta_kp, ruta_fases, nombre_base
            )
        except RuntimeError as e:
            estado_3.update(label="Error en cálculo de ángulos", state="error")
            st.error(str(e))
            st.stop()

        if cacheado_3:
            estado_3.update(
                label=f"⚡ Ángulos calculados — resultado guardado  ({n_params} parámetros)",
                state="complete",
                expanded=False,
            )
        else:
            estado_3.update(
                label=f"✓ {n_params} parámetros biomecánicos calculados",
                state="complete",
                expanded=False,
            )

    # ── Paso 4: Generación de feedback con Claude ─────────────────────────
    with st.status("Generando feedback biomecánico con IA...", expanded=True) as estado_4:
        try:
            texto_feedback, metricas = ejecutar_paso_4(ruta_angulos, nombre_base)
        except RuntimeError as e:
            estado_4.update(label="Error al generar feedback", state="error")
            st.error(str(e))
            st.stop()

        estado_4.update(
            label="✓ Feedback biomecánico generado",
            state="complete",
            expanded=False,
        )

    # Guardar en session_state y relanzar para mostrar los resultados
    st.session_state.analisis_completado = True
    st.session_state.feedback_texto      = texto_feedback
    st.session_state.feedback_metricas   = metricas
    st.session_state.rutas_videos        = {
        "esqueleto": str(ruta_esqueleto),
        "fases":     str(ruta_video_fases),
    }
    st.rerun()


# ── Resultados ───────────────────────────────────────────────────────────────
if not (st.session_state.analisis_completado and st.session_state.feedback_texto):
    st.stop()

st.markdown('<hr class="separador">', unsafe_allow_html=True)

# Feedback en Markdown — Streamlit lo renderiza con negritas, listas y secciones
st.markdown(st.session_state.feedback_texto)

# Caption discreto con tiempo y costo
m = st.session_state.feedback_metricas
if m:
    st.markdown(
        f'<p class="metrica-footer">'
        f'Análisis generado en {m["tiempo_segundos"]} seg '
        f'· Costo estimado: ${m["costo_usd"]} USD'
        f'</p>',
        unsafe_allow_html=True,
    )

st.markdown('<hr class="separador">', unsafe_allow_html=True)

# Videos opcionales en expanders colapsados por defecto
rutas = st.session_state.rutas_videos

if rutas.get("esqueleto") and Path(rutas["esqueleto"]).exists():
    with st.expander("Ver video con esqueleto detectado"):
        st.video(rutas["esqueleto"])
        with open(rutas["esqueleto"], "rb") as vf:
            st.download_button(
                "Descargar video",
                data=vf.read(),
                file_name=Path(rutas["esqueleto"]).name,
                mime="video/mp4",
                key="dl_esqueleto",
            )

if rutas.get("fases") and Path(rutas["fases"]).exists():
    with st.expander("Ver video con fases etiquetadas"):
        st.video(rutas["fases"])
        with open(rutas["fases"], "rb") as vf:
            st.download_button(
                "Descargar video",
                data=vf.read(),
                file_name=Path(rutas["fases"]).name,
                mime="video/mp4",
                key="dl_fases",
            )
