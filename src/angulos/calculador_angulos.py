"""
calculador_angulos.py — Calcula los ángulos articulares biomecánicos del saque.

Flujo:
  1. Lee JSON de keypoints (Hito 1) + JSON de fases (Hito 2).
  2. Calcula ~10 ángulos por frame (serie temporal completa).
  3. Extrae el valor representativo por fase (pico/puntual/rango).
  4. Evalúa cada valor contra los rangos del CLAUDE.md.
  5. Devuelve dict listo para guardar como JSON.

Jugador asumido: DIESTRO. Brazo de raqueta = derecho. Pierna delantera = izquierda.
"""

import numpy as np
from src.angulos.geometria import (
    angulo_entre_tres_puntos,
    flexion_articular,
    angulo_vs_vertical,
    angulo_vs_horizontal,
    diferencia_inclinacion_ejes,
)


# ─────────────────────────────────────────────────────────────
# 1. CONFIGURACIÓN BIOMECÁNICA
# ─────────────────────────────────────────────────────────────
# Cada entrada define cómo extraer y evaluar un parámetro.
#
# Campos:
#   clave_frame        : nombre de la clave en el dict de angulos_por_frame
#   fase_inicio_key    : clave en fases_frames para el inicio de la ventana
#   fase_fin_key       : clave para el fin (None = puntual en fase_inicio)
#   tipo_extraccion    : "pico_max", "pico_min", "puntual", "rango"
#   confiable_2d       : bool
#   rango_ideal_min/max: límites del rango óptimo en grados (None = sin rango)
#   rango_minimo_aceptable: límite inferior alternativo cuando hay discrepancia
#                           entre fuentes (None = no aplica)
#   fuentes            : lista de strings con referencias
#   advertencia        : string o None

PARAMETROS_BIOMEDICOS = {

    "flexion_rodilla_delantera": {
        "clave_frame":             "flexion_rodilla_delantera",
        "fase_inicio_key":         "loading",
        "fase_fin_key":            "cocking",
        "tipo_extraccion":         "pico_max",   # máxima flexión = mayor valor
        "confiable_2d":            True,
        "rango_ideal_min":         54.8,
        "rango_ideal_max":         93.3,
        "rango_minimo_aceptable":  15.0,          # Kovacs & Ellenbecker: mínimo patológico
        "fuentes":                 ["Reid et al.", "Jacquier-Bret & Gorce",
                                    "Kovacs & Ellenbecker"],
        "advertencia":             None,
    },

    "flexion_rodilla_trasera": {
        "clave_frame":             "flexion_rodilla_trasera",
        "fase_inicio_key":         "cocking",    # Trophy = inicio de Cocking
        "fase_fin_key":            "acceleration",
        "tipo_extraccion":         "pico_max",
        "confiable_2d":            True,
        "rango_ideal_min":         51.0,
        "rango_ideal_max":         83.8,
        "rango_minimo_aceptable":  None,
        "fuentes":                 ["Jacquier-Bret & Gorce", "Kovacs & Ellenbecker"],
        "advertencia":             None,
    },

    "inclinacion_tronco_vertical": {
        "clave_frame":             "inclinacion_tronco_vertical",
        "fase_inicio_key":         "cocking",    # Trophy Position = inicio Cocking
        "fase_fin_key":            None,          # puntual
        "tipo_extraccion":         "puntual",
        "confiable_2d":            True,
        "rango_ideal_min":         17.9,
        "rango_ideal_max":         32.1,
        "rango_minimo_aceptable":  None,
        "fuentes":                 ["Jacquier-Bret & Gorce", "Kovacs & Ellenbecker"],
        "advertencia":             None,
    },

    "separacion_lateral": {
        "clave_frame":             "separacion_lateral",
        "fase_inicio_key":         "loading",
        "fase_fin_key":            "cocking",
        "tipo_extraccion":         "pico_max",
        "confiable_2d":            False,
        "rango_ideal_min":         24.2,
        "rango_ideal_max":         39.1,
        "rango_minimo_aceptable":  None,
        "fuentes":                 ["Reid et al."],
        "advertencia":             ("En vista lateral este ángulo captura muy poca "
                                    "información sobre la flexión lateral real (que ocurre "
                                    "en profundidad). Valor orientativo únicamente. "
                                    "Para medición precisa se requiere vista frontal."),
    },

    "mer_hombro_proxy": {
        "clave_frame":             "antebrazo_vs_vertical",
        "fase_inicio_key":         "cocking",
        "fase_fin_key":            None,          # puntual
        "tipo_extraccion":         "puntual",
        "confiable_2d":            False,
        "rango_ideal_min":         100.0,
        "rango_ideal_max":         130.0,
        "rango_minimo_aceptable":  None,
        "fuentes":                 ["Reid et al.", "Kovacs & Ellenbecker",
                                    "Jacquier-Bret & Gorce"],
        "advertencia":             ("Estimación 2D aproximada: ángulo del antebrazo "
                                    "respecto a la vertical durante Cocking. Vista lateral "
                                    "puede subestimar la rotación real. Para medición precisa "
                                    "se requiere captura 3D o vista frontal adicional."),
    },

    "inclinacion_pelvica": {
        "clave_frame":             "inclinacion_pelvica",
        "fase_inicio_key":         "cocking",
        "fase_fin_key":            "acceleration",
        "tipo_extraccion":         "pico_max",
        "confiable_2d":            False,
        "rango_ideal_min":         None,          # "controlada", sin rango numérico
        "rango_ideal_max":         None,
        "rango_minimo_aceptable":  None,
        "fuentes":                 ["Bradley et al."],
        "advertencia":             ("Proxy 2D: ángulo trunk-fémur en la cadera derecha. "
                                    "La inclinación pélvica anterior real requiere referencias "
                                    "óseas (ASIS/PSIS) no disponibles en MediaPipe. "
                                    "Valor informativo, no comparar con rangos clínicos."),
    },

    "abduccion_hombro": {
        "clave_frame":             "abduccion_hombro",
        "fase_inicio_key":         "contact",
        "fase_fin_key":            None,          # puntual
        "tipo_extraccion":         "puntual",
        "confiable_2d":            False,
        "rango_ideal_min":         95.0,
        "rango_ideal_max":         125.0,
        "rango_minimo_aceptable":  None,
        "fuentes":                 ["Kovacs & Ellenbecker", "Jacquier-Bret & Gorce",
                                    "Reid et al."],
        "advertencia":             ("En vista lateral este angulo no captura la abduccion "
                                    "real del hombro (que ocurre en el plano frontal). "
                                    "El valor mide la separacion brazo-tronco en el plano "
                                    "de la imagen, pero no es comparable con rangos del paper "
                                    "que estan en plano frontal. Usar solo como referencia "
                                    "visual del nivel del brazo."),
    },

    "flexion_codo": {
        "clave_frame":             "flexion_codo",
        "fase_inicio_key":         "contact",
        "fase_fin_key":            None,
        "tipo_extraccion":         "puntual",
        "confiable_2d":            True,
        "rango_ideal_min":         16.0,
        "rango_ideal_max":         46.0,
        "rango_minimo_aceptable":  None,
        "fuentes":                 ["Kovacs & Ellenbecker", "Jacquier-Bret & Gorce"],
        "advertencia":             None,
    },

    "inclinacion_tronco_horizontal": {
        "clave_frame":             "inclinacion_tronco_horizontal",
        "fase_inicio_key":         "contact",
        "fase_fin_key":            None,
        "tipo_extraccion":         "puntual",
        "confiable_2d":            True,
        "rango_ideal_min":         41.0,
        "rango_ideal_max":         55.0,
        "rango_minimo_aceptable":  None,
        "fuentes":                 ["Kovacs & Ellenbecker"],
        "advertencia":             None,
    },

    "desviacion_muneca": {
        "clave_frame":             "desviacion_muneca",
        "fase_inicio_key":         "contact",
        "fase_fin_key":            None,
        "tipo_extraccion":         "puntual",
        "confiable_2d":            False,
        "rango_ideal_min":         7.0,
        "rango_ideal_max":         23.0,
        "rango_minimo_aceptable":  None,
        "fuentes":                 ["Kovacs & Ellenbecker"],
        "advertencia":             ("Proxy 2D: desviación del eje mano-antebrazo en el plano "
                                    "de la imagen. La extensión real de muñeca incluye rotación "
                                    "fuera del plano no visible desde vista lateral."),
    },

    "rom_rotacion_interna": {
        "clave_frame":             "antebrazo_vs_vertical",  # misma señal que MER
        "fase_inicio_key":         "deceleration",
        "fase_fin_key":            "finish",
        "tipo_extraccion":         "rango",       # max - min durante Deceleration
        "confiable_2d":            False,
        "rango_ideal_min":         None,          # "rango completo", sin valor numérico
        "rango_ideal_max":         None,
        "rango_minimo_aceptable":  None,
        "fuentes":                 ["Bradley et al."],
        "advertencia":             ("Proxy 2D: rango del ángulo del antebrazo durante "
                                    "la desaceleración. La rotación interna real del hombro "
                                    "requiere medición 3D. Valores bajos (<30°) sugieren "
                                    "posible restricción de RoM."),
    },
}


# ─────────────────────────────────────────────────────────────
# 2. HELPERS
# ─────────────────────────────────────────────────────────────

def _lm_a_dict(landmarks_lista):
    """
    Convierte la lista de landmarks de un frame (formato JSON del Hito 1)
    a un dict {nombre: {x, y, visibility}} para acceso rápido por nombre.
    """
    return {lm["nombre"]: lm for lm in landmarks_lista}


def _punto(lm_dict, nombre, umbral_vis=0.5):
    """
    Extrae las coordenadas (x, y) de un landmark.
    Devuelve None si el landmark no existe o su visibility < umbral.
    """
    lm = lm_dict.get(nombre)
    if lm is None or lm.get("visibility", 0.0) < umbral_vis:
        return None
    return (lm["x"], lm["y"])


def _midpoint(p1, p2):
    """Punto medio entre dos coordenadas (x, y)."""
    return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)


# ─────────────────────────────────────────────────────────────
# 3. FUNCIONES DE ÁNGULO POR FRAME (una por parámetro)
# ─────────────────────────────────────────────────────────────

def calc_flexion_rodilla_delantera(lm):
    """
    Flexión de rodilla delantera (izquierda, jugador diestro).
    Fórmula: flexion_articular(cadera_izq, rodilla_izq, tobillo_izq)
    Devuelve grados de flexión [0°=recta, 90°=escuadra]. None si visibility < 0.5.
    """
    p1 = _punto(lm, "cadera_izq")
    p2 = _punto(lm, "rodilla_izq")
    p3 = _punto(lm, "tobillo_izq")
    if None in (p1, p2, p3):
        return None
    return flexion_articular(p1, p2, p3)


def calc_flexion_rodilla_trasera(lm):
    """
    Flexión de rodilla trasera (derecha, jugador diestro).
    Fórmula: flexion_articular(cadera_der, rodilla_der, tobillo_der)
    Devuelve grados de flexión. None si visibility < 0.5.
    """
    p1 = _punto(lm, "cadera_der")
    p2 = _punto(lm, "rodilla_der")
    p3 = _punto(lm, "tobillo_der")
    if None in (p1, p2, p3):
        return None
    return flexion_articular(p1, p2, p3)


def calc_abduccion_hombro(lm):
    """
    Abducción/Elevación del hombro derecho (brazo de raqueta).
    Fórmula: angulo_entre_tres_puntos(cadera_der, hombro_der, codo_der)
    Ángulo en hombro_der entre línea de tronco y línea del brazo.
    Rango ideal en Contact: 95°–125°. None si visibility < 0.5.
    """
    p_cadera = _punto(lm, "cadera_der")
    p_hombro = _punto(lm, "hombro_der")
    p_codo   = _punto(lm, "codo_der")
    if None in (p_cadera, p_hombro, p_codo):
        return None
    return angulo_entre_tres_puntos(p_cadera, p_hombro, p_codo)


def calc_flexion_codo(lm):
    """
    Flexión del codo derecho (brazo de raqueta).
    Fórmula: flexion_articular(hombro_der, codo_der, muneca_der)
    Devuelve grados de flexión [0°=brazo extendido]. Rango ideal: 16°–46°.
    None si visibility < 0.5.
    """
    p1 = _punto(lm, "hombro_der")
    p2 = _punto(lm, "codo_der")
    p3 = _punto(lm, "muneca_der")
    if None in (p1, p2, p3):
        return None
    return flexion_articular(p1, p2, p3)


def calc_inclinacion_tronco_horizontal(lm):
    """
    Inclinación del tronco sobre la horizontal.
    Fórmula: angulo_vs_horizontal(midpoint_caderas, midpoint_hombros)
    0°=tronco horizontal, 90°=tronco vertical. Rango ideal Contact: 41°–55°.
    None si algún landmark de caderas u hombros < 0.5.
    """
    p_hi = _punto(lm, "hombro_izq")
    p_hd = _punto(lm, "hombro_der")
    p_ci = _punto(lm, "cadera_izq")
    p_cd = _punto(lm, "cadera_der")
    if None in (p_hi, p_hd, p_ci, p_cd):
        return None
    midp_caderas = _midpoint(p_ci, p_cd)
    midp_hombros = _midpoint(p_hi, p_hd)
    return angulo_vs_horizontal(midp_caderas, midp_hombros)


def calc_inclinacion_tronco_vertical(lm):
    """
    Inclinación del tronco respecto a la vertical (forward lean).
    Fórmula: angulo_vs_vertical(midpoint_caderas, midpoint_hombros)
    0°=tronco vertical, 90°=horizontal. Rango ideal Loading/Trophy: 17.9°–32.1°.
    None si algún landmark < 0.5.
    """
    p_hi = _punto(lm, "hombro_izq")
    p_hd = _punto(lm, "hombro_der")
    p_ci = _punto(lm, "cadera_izq")
    p_cd = _punto(lm, "cadera_der")
    if None in (p_hi, p_hd, p_ci, p_cd):
        return None
    midp_caderas = _midpoint(p_ci, p_cd)
    midp_hombros = _midpoint(p_hi, p_hd)
    return angulo_vs_vertical(midp_caderas, midp_hombros)


def calc_separacion_lateral(lm):
    """
    Separación lateral hombro-pelvis (proxy 2D, confiable_2d=False).
    Fórmula: diferencia_inclinacion_ejes(hombro_izq, hombro_der, cadera_izq, cadera_der)
    Diferencia de inclinación entre eje de hombros y eje de caderas.
    Rango ideal: 24.2°–39.1° (vista frontal). Desde lateral: orientativo.
    None si algún landmark < 0.5.
    """
    p_hi = _punto(lm, "hombro_izq")
    p_hd = _punto(lm, "hombro_der")
    p_ci = _punto(lm, "cadera_izq")
    p_cd = _punto(lm, "cadera_der")
    if None in (p_hi, p_hd, p_ci, p_cd):
        return None
    return diferencia_inclinacion_ejes(p_hi, p_hd, p_ci, p_cd)


def calc_antebrazo_vs_vertical(lm):
    """
    Ángulo del antebrazo derecho respecto a la vertical.
    Fórmula: angulo_vs_vertical(codo_der, muneca_der)
    Se usa como:
      - Proxy de MER (confiable_2d=False): ángulo en frame de Cocking.
      - Proxy de RoM rotación interna (confiable_2d=False): rango durante Deceleration.
    None si visibility < 0.5.
    """
    p_codo   = _punto(lm, "codo_der")
    p_muneca = _punto(lm, "muneca_der")
    if None in (p_codo, p_muneca):
        return None
    return angulo_vs_vertical(p_codo, p_muneca)


def calc_inclinacion_pelvica(lm):
    """
    Inclinación pélvica anterior (proxy 2D, confiable_2d=False).
    Fórmula: angulo_entre_tres_puntos(hombro_der, cadera_der, rodilla_der)
    Ángulo trunk-fémur en la cadera derecha. Sin rango numérico en CLAUDE.md.
    None si visibility < 0.5.
    """
    p_hombro = _punto(lm, "hombro_der")
    p_cadera = _punto(lm, "cadera_der")
    p_rodilla = _punto(lm, "rodilla_der")
    if None in (p_hombro, p_cadera, p_rodilla):
        return None
    return angulo_entre_tres_puntos(p_hombro, p_cadera, p_rodilla)


def calc_desviacion_muneca(lm):
    """
    Desviación/extensión de muñeca derecha (proxy 2D, confiable_2d=False).
    Fórmula: flexion_articular(codo_der, muneca_der, indice_der)
    Desviación del eje mano-antebrazo. 0°=muñeca recta. Rango ideal: 7°–23°.
    None si visibility < 0.5.
    """
    p_codo   = _punto(lm, "codo_der")
    p_muneca = _punto(lm, "muneca_der")
    p_indice = _punto(lm, "indice_der")
    if None in (p_codo, p_muneca, p_indice):
        return None
    return flexion_articular(p_codo, p_muneca, p_indice)


# ─────────────────────────────────────────────────────────────
# 4. CÁLCULO DE TODOS LOS ÁNGULOS DE UN FRAME
# ─────────────────────────────────────────────────────────────

# Mapa de función por clave (para iterar en calcular_angulos_frame)
_FUNCIONES_POR_CLAVE = {
    "flexion_rodilla_delantera":    calc_flexion_rodilla_delantera,
    "flexion_rodilla_trasera":      calc_flexion_rodilla_trasera,
    "abduccion_hombro":             calc_abduccion_hombro,
    "flexion_codo":                 calc_flexion_codo,
    "inclinacion_tronco_horizontal": calc_inclinacion_tronco_horizontal,
    "inclinacion_tronco_vertical":  calc_inclinacion_tronco_vertical,
    "separacion_lateral":           calc_separacion_lateral,
    "antebrazo_vs_vertical":        calc_antebrazo_vs_vertical,
    "inclinacion_pelvica":          calc_inclinacion_pelvica,
    "desviacion_muneca":            calc_desviacion_muneca,
}


def calcular_angulos_frame(lm_dict):
    """
    Calcula todos los ángulos para un frame dado.

    Parámetros:
        lm_dict : dict {nombre_landmark: {x, y, visibility, ...}}
                  (resultado de _lm_a_dict sobre la lista de landmarks del frame)

    Retorna:
        dict: {clave_angulo: float_o_None, ...}
              None indica que algún landmark clave tenía visibility < 0.5.
    """
    return {clave: func(lm_dict) for clave, func in _FUNCIONES_POR_CLAVE.items()}


# ─────────────────────────────────────────────────────────────
# 5. EXTRACCIÓN DE VALOR REPRESENTATIVO POR FASE
# ─────────────────────────────────────────────────────────────

def extraer_valor_por_fase(serie, fase_inicio, fase_fin, tipo):
    """
    Extrae el valor representativo de una serie temporal en una ventana de fase.

    Parámetros:
        serie       : lista de floats o None (uno por frame, indexada por frame)
        fase_inicio : frame de inicio de la ventana (inclusive)
        fase_fin    : frame de fin de la ventana (exclusive). None si tipo="puntual".
        tipo        : "puntual" | "pico_max" | "pico_min" | "rango"

    Retorna:
        tuple (valor, frame_referencia):
            valor           : float o None
            frame_referencia: frame donde se encontró el valor (o fase_inicio si puntual)

    Tipos:
        puntual  : devuelve el valor en frame = fase_inicio
        pico_max : máximo de la ventana (ignora None)
        pico_min : mínimo de la ventana (ignora None)
        rango    : max - min de la ventana (ignora None). Devuelve None si < 2 valores.
    """
    if tipo == "puntual":
        idx = min(fase_inicio, len(serie) - 1)
        return serie[idx], idx

    # Para pico_max, pico_min, rango: trabajamos con la ventana
    fin = min(fase_fin, len(serie)) if fase_fin is not None else len(serie)
    ventana = [(i, v) for i, v in enumerate(serie[fase_inicio:fin], start=fase_inicio)
               if v is not None]

    if not ventana:
        return None, fase_inicio

    if tipo == "pico_max":
        frame_ref, valor = max(ventana, key=lambda x: x[1])
        return valor, frame_ref

    if tipo == "pico_min":
        frame_ref, valor = min(ventana, key=lambda x: x[1])
        return valor, frame_ref

    if tipo == "rango":
        if len(ventana) < 2:
            return None, fase_inicio
        valores = [v for _, v in ventana]
        return max(valores) - min(valores), fase_inicio

    return None, fase_inicio


# ─────────────────────────────────────────────────────────────
# 6. EVALUACIÓN CONTRA RANGOS BIOMECÁNICOS
# ─────────────────────────────────────────────────────────────

def evaluar_angulo(valor, config):
    """
    Evalúa un valor angular contra el rango ideal y el rango mínimo aceptable.

    Retorna:
        str: "optimo"     → dentro del rango ideal [rango_ideal_min, rango_ideal_max]
             "aceptable"  → entre rango_minimo_aceptable y rango_ideal_min
             "deficiente" → por debajo de rango_minimo_aceptable
             "excesivo"   → por encima de rango_ideal_max
             "no_evaluable" → valor es None o no hay rangos definidos
    """
    if valor is None:
        return "no_evaluable"

    r_min  = config.get("rango_ideal_min")
    r_max  = config.get("rango_ideal_max")
    r_acep = config.get("rango_minimo_aceptable")

    # Sin rango definido en el paper (e.g. inclinación pélvica, RoM)
    if r_min is None or r_max is None:
        return "no_evaluable"

    if r_min <= valor <= r_max:
        return "optimo"

    if valor > r_max:
        return "excesivo"

    # valor < r_min
    if r_acep is not None and valor >= r_acep:
        return "aceptable"

    return "deficiente"


# ─────────────────────────────────────────────────────────────
# 7. ORQUESTADOR PRINCIPAL
# ─────────────────────────────────────────────────────────────

def calcular_todos_los_angulos(datos_keypoints, datos_fases):
    """
    Orquestador completo del Hito 3.

    Parámetros:
        datos_keypoints : dict cargado del JSON del Hito 1
                          (tiene clave "frames" con lista de frames)
        datos_fases     : dict cargado del JSON del Hito 2
                          (tiene clave "fases" con {nombre: {"frame": N}})

    Retorna:
        dict listo para serializar como JSON:
        {
            "video": str,
            "angulos_por_frame": [{"frame": N, "angulos": {...}}, ...],
            "resumen_por_fase": {nombre_parametro: {...}, ...}
        }
    """
    nombre_video = datos_keypoints.get("video", "desconocido")
    frames       = datos_keypoints["frames"]
    n            = len(frames)

    # Extraer frame de inicio de cada fase como entero simple
    fases_frames = {
        fase: datos["frame"]
        for fase, datos in datos_fases["fases"].items()
    }

    print(f"\n{'='*60}")
    print(f"Calculando ángulos en: {nombre_video}")
    print(f"Total frames: {n} | Fases detectadas: {list(fases_frames.keys())}")
    print(f"{'='*60}\n")

    # ── Paso 1: calcular ángulos frame a frame ─────────────────
    angulos_por_frame = []
    # Para cada clave de ángulo, guardamos la serie temporal (lista de floats/None)
    series = {clave: [] for clave in _FUNCIONES_POR_CLAVE}

    for frame_data in frames:
        frame_idx = frame_data["frame"]
        lm_dict   = _lm_a_dict(frame_data["landmarks"])
        resultado = calcular_angulos_frame(lm_dict)

        angulos_por_frame.append({
            "frame":   frame_idx,
            "angulos": {k: (round(v, 2) if v is not None else None)
                        for k, v in resultado.items()}
        })

        for clave in series:
            series[clave].append(resultado[clave])

    print(f"  Series temporales calculadas ({n} frames por ángulo).")

    # ── Paso 2: extraer valor representativo por fase ──────────
    resumen_por_fase = {}

    for nombre_param, config in PARAMETROS_BIOMEDICOS.items():
        clave_frame  = config["clave_frame"]
        tipo         = config["tipo_extraccion"]
        inicio_key   = config["fase_inicio_key"]
        fin_key      = config["fase_fin_key"]

        # Obtener frame de inicio y fin de la ventana
        frame_inicio = fases_frames.get(inicio_key)
        frame_fin    = fases_frames.get(fin_key) if fin_key else None

        if frame_inicio is None:
            print(f"  ADVERTENCIA: fase '{inicio_key}' no encontrada para {nombre_param}")
            valor, frame_ref = None, 0
        else:
            serie = series[clave_frame]
            valor, frame_ref = extraer_valor_por_fase(serie, frame_inicio, frame_fin, tipo)

        evaluacion = evaluar_angulo(valor, config)

        # Construir la entrada del resumen
        entrada = {
            "valor":              round(valor, 2) if valor is not None else None,
            "unidad":             "grados",
            "tipo_extraccion":    tipo,
            "fase":               inicio_key,
            "frame_referencia":   int(frame_ref),
            "confiable_2d":       config["confiable_2d"],
            "rango_ideal_min":    config["rango_ideal_min"],
            "rango_ideal_max":    config["rango_ideal_max"],
            "fuentes":            config["fuentes"],
            "evaluacion":         evaluacion,
        }

        # Añadir campos opcionales solo si aplican
        if config.get("rango_minimo_aceptable") is not None:
            entrada["rango_minimo_aceptable"] = config["rango_minimo_aceptable"]
        if config.get("advertencia") is not None:
            entrada["advertencia"] = config["advertencia"]

        resumen_por_fase[nombre_param] = entrada

        estado = f"{valor:.1f}°" if valor is not None else "None"
        print(f"  {nombre_param:35s}  {estado:10s}  [{evaluacion}]")

    print(f"\n{'='*60}")
    print("Cálculo completado.\n")

    return {
        "video":             nombre_video,
        "angulos_por_frame": angulos_por_frame,
        "resumen_por_fase":  resumen_por_fase,
    }
