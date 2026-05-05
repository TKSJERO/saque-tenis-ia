"""
geometria.py — Funciones geométricas para el cálculo de ángulos articulares.

CONVENCIONES IMPORTANTES:
  - Todos los cálculos usan solo X,Y (2D). La coordenada Z de MediaPipe
    se ignora por ser una estimación con error significativo.
  - En MediaPipe: Y=0 es la parte SUPERIOR de la imagen, Y=1 es la INFERIOR.
    Por eso dy negativo = movimiento hacia arriba en el frame.
  - Los puntos (p) son tuplas o arrays de dos elementos: (x, y).
  - Todos los ángulos se devuelven en GRADOS (°), no en radianes.
  - Los resultados están siempre en [0°, 180°] para ángulos articulares
    y en [0°, 90°] para inclinaciones respecto a ejes.

OBSERVACIÓN DE CALIBRACIÓN:
  Las mediciones iniciales del video_pro.mp4 muestran un tronco en Contact
  a ~79° de la horizontal, mientras el paper indica rango ideal 41°–55°.
  Esta discrepancia puede deberse a: (1) técnica específica del pro,
  (2) diferencia en el punto de referencia del "tronco" entre papers
  (algunos usan cadera→C7, otros cadera→hombros), (3) diferencia entre
  vista lateral 2D y medición 3D real. Pendiente de investigación en
  Hito 4 antes de dar feedback.
"""

import numpy as np


# ─────────────────────────────────────────────────────────────
# 1. ÁNGULO ARTICULAR (3 puntos)
# ─────────────────────────────────────────────────────────────

def angulo_entre_tres_puntos(p1, p2, p3):
    """
    Calcula el ángulo en el vértice p2, formado por los segmentos p2→p1 y p2→p3.
    Resultado en [0°, 180°]. 0° = los tres puntos coinciden en una línea con
    p2 en el extremo. 180° = los tres puntos son colineales con p2 en el centro
    (articulación completamente extendida).

    Fórmula:
        v1 = p1 - p2   (vector de p2 hacia p1)
        v2 = p3 - p2   (vector de p2 hacia p3)
        ángulo = arccos( dot(v1, v2) / (|v1| × |v2|) )

    Parámetros:
        p1, p2, p3 : tupla (x, y) o array de 2 elementos

    Retorna:
        float: ángulo en grados en el vértice p2. Devuelve 0.0 si algún
               vector tiene norma ~0 (puntos coincidentes).

    Ejemplos verificables a mano:
    ─────────────────────────────
    Ejemplo 1 — Ángulo recto (90°):
        p1 = (0, 0)   p2 = (1, 0)   p3 = (1, 1)
        v1 = p1 - p2 = (-1,  0)
        v2 = p3 - p2 = ( 0,  1)
        dot(v1, v2) = (-1)×0 + 0×1 = 0
        arccos(0) = 90°  ✓

    Ejemplo 2 — Línea recta (180°, articulación extendida):
        p1 = (0, 0)   p2 = (1, 0)   p3 = (2, 0)
        v1 = (-1, 0)   v2 = (1, 0)
        dot(v1_norm, v2_norm) = -1
        arccos(-1) = 180°  ✓

    Ejemplo 3 — Ángulo de 45°:
        p1 = (0, 1)   p2 = (0, 0)   p3 = (1, 1)
        v1 = (0, 1)   v2 = (1, 1)
        v2_norm = (1/√2, 1/√2)
        dot(v1_norm, v2_norm) = 0×(1/√2) + 1×(1/√2) = 1/√2 ≈ 0.7071
        arccos(0.7071) = 45°  ✓
    """
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)
    p3 = np.asarray(p3, dtype=float)

    v1 = p1 - p2
    v2 = p3 - p2

    norma1 = np.linalg.norm(v1)
    norma2 = np.linalg.norm(v2)

    if norma1 < 1e-6 or norma2 < 1e-6:
        # Puntos coincidentes: ángulo indefinido, devolvemos 0
        return 0.0

    coseno = np.dot(v1, v2) / (norma1 * norma2)
    # Clamp para evitar errores numéricos fuera de [-1, 1]
    coseno = np.clip(coseno, -1.0, 1.0)
    return float(np.degrees(np.arccos(coseno)))


# ─────────────────────────────────────────────────────────────
# 2. FLEXIÓN ARTICULAR
# ─────────────────────────────────────────────────────────────

def flexion_articular(p_proximal, p_vertice, p_distal):
    """
    Calcula el ángulo de FLEXIÓN en la articulación (vértice).
    Flexión = 180° − ángulo_articular.

    Convenio:
        0°   = articulación completamente extendida (recta)
        90°  = flexión de 90°
        180° = completamente doblada sobre sí misma

    Se usa para rodillas, codo y muñeca, donde los rangos biomecánicos
    del CLAUDE.md están expresados como grados de flexión (no ángulos
    articulares).

    Parámetros:
        p_proximal : punto proximal (e.g. cadera para rodilla)
        p_vertice  : articulación a medir (e.g. rodilla)
        p_distal   : punto distal (e.g. tobillo para rodilla)

    Retorna:
        float: flexión en grados en [0°, 180°].

    Ejemplos verificables a mano:
    ─────────────────────────────
    Ejemplo 1 — Pierna recta (0° de flexión):
        p_proximal = (0, 0)   p_vertice = (0, 1)   p_distal = (0, 2)
        ángulo_articular = angulo_entre_tres_puntos → 180°
        flexión = 180° − 180° = 0°  ✓

    Ejemplo 2 — Flexión de 90° (rodilla en escuadra):
        p_proximal = (0, 0)   p_vertice = (0, 1)   p_distal = (1, 1)
        v1 = (0,-1)   v2 = (1,0)
        dot = 0  →  ángulo_articular = 90°
        flexión = 180° − 90° = 90°  ✓

    Ejemplo 3 — Flexión de 45°:
        p_proximal = (0, 0)   p_vertice = (0, 1)   p_distal = (1, 2)
        v1 = (0,-1)   v2 = (1,1) → v2_norm = (1/√2, 1/√2)
        dot = 0×(1/√2) + (−1)×(1/√2) = −1/√2  →  ángulo = 135°
        flexión = 180° − 135° = 45°  ✓
    """
    articular = angulo_entre_tres_puntos(p_proximal, p_vertice, p_distal)
    return 180.0 - articular


# ─────────────────────────────────────────────────────────────
# 3. INCLINACIÓN RESPECTO A EJES
# ─────────────────────────────────────────────────────────────

def angulo_vs_vertical(p1, p2):
    """
    Ángulo del vector p1→p2 respecto al eje VERTICAL (eje Y de la imagen).
    Resultado en [0°, 90°].

        0°  = vector perfectamente vertical (apunta recto arriba o abajo)
        90° = vector perfectamente horizontal

    NOTA sobre el eje Y de MediaPipe: Y aumenta hacia abajo (0=arriba, 1=abajo).
    Esta función toma el valor absoluto de ambas componentes antes de calcular,
    por lo que es independiente de si el vector apunta hacia arriba o hacia abajo.

    Uso típico:
        - Inclinación del tronco (cadera_media → hombro_media): cuánto se aleja
          el tronco de la vertical. 0° = jugador de pie recto.
        - Inclinación del antebrazo para proxy de MER.

    Parámetros:
        p1, p2 : tupla (x, y) o array de 2 elementos

    Retorna:
        float: ángulo en grados en [0°, 90°]. Devuelve 0.0 si los puntos
               son coincidentes.

    Ejemplos verificables a mano:
    ─────────────────────────────
    Ejemplo 1 — Vector vertical (0°):
        p1 = (0.5, 0.7)   p2 = (0.5, 0.3)
        dx = 0.0   dy = -0.4
        arctan2(|0.0|, |−0.4|) = arctan2(0.0, 0.4) = arctan(0) = 0°  ✓

    Ejemplo 2 — Vector horizontal (90°):
        p1 = (0.0, 0.5)   p2 = (0.5, 0.5)
        dx = 0.5   dy = 0.0
        arctan2(|0.5|, |0.0|) = arctan2(0.5, 0.0) = 90°  ✓

    Ejemplo 3 — Diagonal 45°:
        p1 = (0.0, 0.0)   p2 = (1.0, 1.0)
        dx = 1.0   dy = 1.0
        arctan2(1.0, 1.0) = 45°  ✓

    Ejemplo 4 — Tronco inclinado ~20° hacia adelante (típico Loading):
        p1 = (0.47, 0.62)   p2 = (0.50, 0.54)
        dx = 0.03   dy = -0.08
        arctan2(0.03, 0.08) ≈ arctan(0.375) ≈ 20.6°  ✓
    """
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)

    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    norma = np.sqrt(dx**2 + dy**2)
    if norma < 1e-6:
        return 0.0

    return float(np.degrees(np.arctan2(abs(dx), abs(dy))))


def angulo_vs_horizontal(p1, p2):
    """
    Ángulo del vector p1→p2 respecto al eje HORIZONTAL.
    Resultado en [0°, 90°]. Es el complemento de angulo_vs_vertical:
        angulo_vs_horizontal = 90° − angulo_vs_vertical

        0°  = vector perfectamente horizontal
        90° = vector perfectamente vertical

    Uso típico:
        - Inclinación del tronco sobre la horizontal en Contact (rango ideal
          41°–55°). Si el ángulo es 48°, el tronco está a 48° de la horizontal
          (o sea, 42° de la vertical).

    Parámetros:
        p1, p2 : tupla (x, y) o array de 2 elementos

    Retorna:
        float: ángulo en grados en [0°, 90°].

    Ejemplos verificables a mano:
    ─────────────────────────────
    Ejemplo 1 — Vector horizontal (0°):
        p1 = (0.0, 0.5)   p2 = (0.5, 0.5)
        angulo_vs_vertical = 90°  →  90° − 90° = 0°  ✓

    Ejemplo 2 — Vector vertical (90°):
        p1 = (0.5, 0.7)   p2 = (0.5, 0.3)
        angulo_vs_vertical = 0°   →  90° − 0°  = 90°  ✓

    Ejemplo 3 — Diagonal 45°:
        p1 = (0.0, 0.0)   p2 = (1.0, 1.0)
        angulo_vs_vertical = 45°  →  90° − 45° = 45°  ✓

    Ejemplo 4 — Tronco en Contact (~11° de vertical = ~79° de horizontal):
        p1 = (0.465, 0.621)   p2 = (0.487, 0.508)
        dx=0.022  dy=-0.113
        angulo_vs_vertical ≈ arctan2(0.022, 0.113) ≈ 11°
        angulo_vs_horizontal ≈ 90° − 11° = 79°
        (Indica tronco muy vertical en ese frame del video de prueba)
    """
    return 90.0 - angulo_vs_vertical(p1, p2)


# ─────────────────────────────────────────────────────────────
# 4. SEPARACIÓN ENTRE DOS EJES (proxy de flexión lateral)
# ─────────────────────────────────────────────────────────────

def diferencia_inclinacion_ejes(p1a, p1b, p2a, p2b):
    """
    Diferencia de inclinación (respecto a la horizontal) entre dos ejes
    de segmentos: eje 1 = línea p1a→p1b, eje 2 = línea p2a→p2b.

    Se usa como proxy 2D de la "separación por flexión lateral hombro-pelvis":
        eje 1 = hombro_izq → hombro_der
        eje 2 = cadera_izq → cadera_der

    ADVERTENCIA DE CONFIABILIDAD: desde vista lateral del video, ambos ejes
    (hombros y caderas) están orientados en profundidad. Esta función mide
    la diferencia de inclinación que SÍ es visible en el plano de la imagen.
    El valor captura muy poca información de la flexión lateral real.
    Usar solo como orientación; no comparar directamente con rangos 3D del paper.

    Parámetros:
        p1a, p1b : extremos del eje 1 (e.g. hombro_izq, hombro_der)
        p2a, p2b : extremos del eje 2 (e.g. cadera_izq, cadera_der)

    Retorna:
        float: diferencia absoluta de inclinación en grados [0°, 90°].

    Ejemplos verificables a mano:
    ─────────────────────────────
    Ejemplo 1 — Ambos ejes horizontales (0° de separación):
        p1a=(0,0)  p1b=(1,0)   p2a=(0,0.5)  p2b=(1,0.5)
        inclinación eje1 = 0°  (horizontal)
        inclinación eje2 = 0°  (horizontal)
        diferencia = |0° − 0°| = 0°  ✓

    Ejemplo 2 — Un eje a 10° del otro:
        p1a=(0,0)  p1b=(1,0)       →  eje1 = horizontal = 0°
        p2a=(0,0)  p2b=(1,0.176)   →  eje2 ≈ arctan(0.176/1) ≈ 10° de la horizontal
        diferencia ≈ |0° − 10°| = 10°  ✓
    """
    inc_eje1 = angulo_vs_horizontal(p1a, p1b)
    inc_eje2 = angulo_vs_horizontal(p2a, p2b)
    return abs(inc_eje1 - inc_eje2)
