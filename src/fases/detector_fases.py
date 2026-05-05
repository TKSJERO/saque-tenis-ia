"""
detector_fases.py — Detecta las 8 fases del saque de tenis a partir de keypoints.

IMPORTANTE: En MediaPipe el eje Y va de 0 (arriba de la imagen) a 1 (abajo).
Por eso:
  - "máximo Y" (valor numérico alto) = punto más bajo del cuerpo en el frame
  - "mínimo Y" (valor numérico bajo) = punto más alto del cuerpo en el frame
Esto es el error #1 cuando se trabaja con coordenadas de imagen.
Todos los comentarios de detección usan esta convención explícitamente.

Señales proxy del cuerpo (no hay pelota ni raqueta en los datos):
  - Pelota proxy → movimiento de muneca_izq (mano de lanzamiento, jugador diestro)
  - Raqueta proxy → movimiento de muneca_der (mano de raqueta, jugador diestro)
"""

import json
import numpy as np
from pathlib import Path


# Etiquetas legibles para mostrar en el video y en los logs
ETIQUETAS_FASES = {
    "pre_start":     "Pre-Inicio",
    "start":         "1. Start",
    "release":       "2. Release",
    "loading":       "3. Loading",
    "cocking":       "4. Cocking",
    "acceleration":  "5. Acceleration",
    "contact":       "6. Contact",
    "deceleration":  "7. Deceleration",
    "finish":        "8. Finish",
}

# Orden de las fases (para asignar etiqueta a cada frame)
ORDEN_FASES = [
    "start", "release", "loading", "cocking",
    "acceleration", "contact", "deceleration", "finish",
]


# ─────────────────────────────────────────────
# 1. CARGA Y EXTRACCIÓN DE SEÑALES
# ─────────────────────────────────────────────

def cargar_keypoints(ruta_json):
    """Lee el JSON de keypoints generado por el Hito 1."""
    with open(ruta_json, "r", encoding="utf-8") as f:
        return json.load(f)


def extraer_señales(frames):
    """
    Extrae las series temporales Y (y X donde sea necesario) de los
    landmarks clave, frame a frame.

    Para jugador DIESTRO:
      - Brazo de raqueta  = derecho → hombro_der, codo_der, muneca_der
      - Brazo de lanzamiento = izquierdo → muneca_izq
      - Rodilla delantera = izquierda → rodilla_izq
    """
    n = len(frames)

    señales = {
        nombre: np.zeros(n)
        for nombre in [
            "muneca_izq_y", "muneca_izq_x",
            "muneca_der_y", "muneca_der_x",
            "hombro_izq_y", "hombro_der_y",
            "cadera_izq_y", "cadera_der_y", "cadera_media_y",
            "rodilla_izq_y", "rodilla_der_y",
            "tobillo_izq_y", "tobillo_der_y",
        ]
    }
    señales["pose_detectada"] = np.zeros(n, dtype=bool)

    for i, frame in enumerate(frames):
        señales["pose_detectada"][i] = frame["pose_detectada"]
        if not frame["pose_detectada"]:
            continue

        # Convertir lista de landmarks a dict por nombre para acceso rápido
        lm = {lm_item["nombre"]: lm_item for lm_item in frame["landmarks"]}

        señales["muneca_izq_y"][i] = lm["muneca_izq"]["y"]
        señales["muneca_izq_x"][i] = lm["muneca_izq"]["x"]
        señales["muneca_der_y"][i] = lm["muneca_der"]["y"]
        señales["muneca_der_x"][i] = lm["muneca_der"]["x"]
        señales["hombro_izq_y"][i] = lm["hombro_izq"]["y"]
        señales["hombro_der_y"][i] = lm["hombro_der"]["y"]
        señales["cadera_izq_y"][i] = lm["cadera_izq"]["y"]
        señales["cadera_der_y"][i] = lm["cadera_der"]["y"]
        señales["cadera_media_y"][i] = (lm["cadera_izq"]["y"] + lm["cadera_der"]["y"]) / 2
        señales["rodilla_izq_y"][i] = lm["rodilla_izq"]["y"]
        señales["rodilla_der_y"][i] = lm["rodilla_der"]["y"]
        señales["tobillo_izq_y"][i] = lm["tobillo_izq"]["y"]
        señales["tobillo_der_y"][i] = lm["tobillo_der"]["y"]

    return señales


# ─────────────────────────────────────────────
# 2. UTILIDADES DE SEÑAL
# ─────────────────────────────────────────────

def suavizar(serie, ventana=9):
    """
    Media móvil (rolling average) para reducir el ruido del sensor.
    Ventana de 9 frames ≈ 0.3 segundos a 30 fps.
    """
    kernel = np.ones(ventana) / ventana
    return np.convolve(serie, kernel, mode="same")


def indice_maximo_local(serie, desde, hasta):
    """
    Devuelve el índice del valor máximo de `serie` en el rango [desde, hasta).
    Y máximo = punto más bajo en la imagen.
    Si el rango está vacío o fuera del array, devuelve el último índice válido.
    """
    n = len(serie)
    desde = min(desde, n - 1)   # cota: nunca pedir más allá del array
    hasta = min(hasta, n)
    segmento = serie[desde:hasta]
    if len(segmento) == 0:
        return desde
    return desde + int(np.argmax(segmento))


def indice_minimo_local(serie, desde, hasta):
    """
    Devuelve el índice del valor mínimo de `serie` en el rango [desde, hasta).
    Y mínimo = punto más alto en la imagen.
    Si el rango está vacío o fuera del array, devuelve el último índice válido.
    """
    n = len(serie)
    desde = min(desde, n - 1)   # cota: nunca pedir más allá del array
    hasta = min(hasta, n)
    segmento = serie[desde:hasta]
    if len(segmento) == 0:
        return desde
    return desde + int(np.argmin(segmento))


def primer_frame_con_tendencia(serie, desde, hasta, umbral, ventana_confirmacion=8):
    """
    Busca el primer frame en [desde, hasta) donde la serie supera `umbral`
    de manera sostenida (`ventana_confirmacion` frames consecutivos).
    Si no lo encuentra, devuelve el frame de inicio acotado al rango del array.
    """
    hasta = min(hasta, len(serie))
    for i in range(desde, hasta - ventana_confirmacion):
        if all(serie[i:i + ventana_confirmacion] > umbral):
            return i
    return min(desde, len(serie) - 1)   # cota: nunca devolver índice fuera del array


# ─────────────────────────────────────────────
# 3. DETECTOR PRINCIPAL (MÁQUINA DE ESTADOS)
# ─────────────────────────────────────────────

def detectar_fases(ruta_json):
    """
    Lee el JSON de keypoints y detecta el frame de inicio de cada fase.

    Retorna:
        dict: {"start": frame, "release": frame, ..., "finish": frame}
    """
    datos = cargar_keypoints(ruta_json)
    frames = datos["frames"]
    n = len(frames)
    fps = datos.get("fps", 30.0)

    print(f"\n{'='*60}")
    print(f"Detectando fases en: {datos['video']}")
    print(f"Total frames: {n} | FPS: {fps}")
    print(f"{'='*60}\n")

    # Extraer y suavizar señales clave
    s = extraer_señales(frames)

    muneca_izq_y  = suavizar(s["muneca_izq_y"],  ventana=9)
    muneca_izq_x  = suavizar(s["muneca_izq_x"],  ventana=9)
    muneca_der_y  = suavizar(s["muneca_der_y"],  ventana=9)
    muneca_der_x  = suavizar(s["muneca_der_x"],  ventana=9)
    hombro_der_y  = suavizar(s["hombro_der_y"],  ventana=9)
    cadera_y      = suavizar(s["cadera_media_y"], ventana=11)
    tobillo_izq_y = suavizar(s["tobillo_izq_y"], ventana=9)

    # Distancia euclidiana entre muñecas (proxy de separación de manos)
    dist_munecas = np.sqrt(
        (muneca_izq_x - muneca_der_x) ** 2 +
        (muneca_izq_y - muneca_der_y) ** 2
    )
    dist_munecas = suavizar(dist_munecas, ventana=9)

    # Velocidad absoluta de muneca_izq en Y (para detectar movimiento inicial)
    vel_izq_y = np.abs(np.diff(s["muneca_izq_y"], prepend=s["muneca_izq_y"][0]))
    vel_izq_y = suavizar(vel_izq_y, ventana=15)

    fases = {}

    # ── FASE 1: START ──────────────────────────────────────────────────────
    # El jugador empieza a moverse desde la posición estática.
    # Señal: velocidad de muneca_izq Y supera umbral de movimiento de forma
    # sostenida (descarta micro-movimientos).
    # Buscamos en el primer cuarto del video (no el tercio): fuerza a encontrar
    # el movimiento inicial más temprano y evita confundir movimientos tardíos.
    # Corrección A: umbral bajado de 0.0015 a 0.0007, ventana [5, n//4].
    UMBRAL_MOVIMIENTO = 0.0007
    frame_start = primer_frame_con_tendencia(
        vel_izq_y, desde=5, hasta=n // 4,
        umbral=UMBRAL_MOVIMIENTO, ventana_confirmacion=6
    )
    fases["start"] = frame_start
    print(f"[Fase 1 - Start]        frame {frame_start:4d} "
          f"(vel_muneca_izq = {vel_izq_y[frame_start]:.5f})")

    # ── FASE 2: RELEASE ────────────────────────────────────────────────────
    # La pelota abandona la mano izquierda. Señal: la muñeca izquierda
    # (mano de lanzamiento) cruza por encima del punto medio del torso
    # izquierdo (hombro_izq + cadera_izq) / 2, de forma sostenida.
    # Justificación biomecánica: cuando la muñeca está claramente más alta
    # que el torso medio, el toss ya está "bien arriba" y la pelota se soltó.
    # Umbral: diff < -0.05 (5% del alto del frame) durante 5 frames → evita
    # falsos positivos del cruce inicial gradual (que ocurre ~20 frames antes).
    hombro_izq_y = suavizar(s["hombro_izq_y"], ventana=9)
    cadera_izq_y_s = suavizar(s["cadera_izq_y"], ventana=9)
    torso_medio_y = (hombro_izq_y + cadera_izq_y_s) / 2
    diff_muneca_torso = muneca_izq_y - torso_medio_y  # negativo = muñeca más alta

    UMBRAL_TOSS = -0.05
    buscar_hasta_release = int(n * 0.60)
    frame_release = primer_frame_con_tendencia(
        -diff_muneca_torso,  # negamos para usar "mayor que umbral"
        desde=frame_start + 10,
        hasta=buscar_hasta_release,
        umbral=-UMBRAL_TOSS,  # busca diff < -0.05 → -diff > 0.05
        ventana_confirmacion=5
    )

    fases["release"] = frame_release
    print(f"[Fase 2 - Release]      frame {frame_release:4d} "
          f"(muneca_izq_y={muneca_izq_y[frame_release]:.4f}, "
          f"torso_medio_y={torso_medio_y[frame_release]:.4f}, "
          f"diff={diff_muneca_torso[frame_release]:+.4f})")

    # ── FASE 3: LOADING ────────────────────────────────────────────────────
    # El cuerpo empieza a descender (carga de piernas).
    # Señal: cadera_media Y empieza a aumentar sostenidamente después de
    # Release (Y más alto = cuerpo más bajo en la imagen).
    referencia_cadera = cadera_y[frame_release]
    UMBRAL_CARGA = 0.008  # desplazamiento vertical mínimo para confirmar carga
    frame_loading = primer_frame_con_tendencia(
        cadera_y - referencia_cadera,
        desde=frame_release + 5,
        hasta=int(n * 0.75),
        umbral=UMBRAL_CARGA,
        ventana_confirmacion=6
    )
    fases["loading"] = frame_loading
    print(f"[Fase 3 - Loading]      frame {frame_loading:4d} "
          f"(cadera_y = {cadera_y[frame_loading]:.4f}, "
          f"referencia = {referencia_cadera:.4f})")

    # ── FASE 4: COCKING ────────────────────────────────────────────────────
    # Trophy Position: cuerpo en su punto más bajo (máxima flexión de rodillas).
    # Señal: cadera_media Y alcanza su máximo local en la ventana de carga.
    # NOTA: Y máximo = abajo en la imagen = cuerpo más bajo.
    frame_cocking = indice_maximo_local(
        cadera_y,
        desde=frame_loading + 15,
        hasta=int(n * 0.75)
    )
    fases["cocking"] = frame_cocking
    print(f"[Fase 4 - Cocking]      frame {frame_cocking:4d} "
          f"(cadera_y máximo = {cadera_y[frame_cocking]:.4f})")

    # ── FASE 5: ACCELERATION ──────────────────────────────────────────────
    # Inicio del swing hacia arriba (arm acceleration).
    # Corrección D: la señal "máximo local de muneca_der_y" no funciona porque
    # en este video la muñeca sube continuamente desde Cocking hasta Contact
    # sin un "dip" claro antes. El máximo que encontrábamos era el follow-through.
    # Nueva señal: primer frame después de Cocking donde la velocidad de
    # muneca_der_y es negativa (Y bajando = brazo subiendo) de manera sostenida
    # durante 5 frames consecutivos con magnitud > umbral.
    # NOTA: velocidad negativa en Y = Y disminuye = brazo sube en la imagen.
    vel_muneca_der = np.diff(muneca_der_y, prepend=muneca_der_y[0])
    UMBRAL_SWING = 0.005  # descenso mínimo de Y por frame para confirmar swing explosivo
    frame_acceleration = primer_frame_con_tendencia(
        -vel_muneca_der,  # negamos para buscar con "mayor que umbral"
        desde=frame_cocking + 5,
        hasta=min(n, frame_cocking + 120),
        umbral=UMBRAL_SWING,
        ventana_confirmacion=5
    )
    fases["acceleration"] = frame_acceleration
    print(f"[Fase 5 - Acceleration] frame {frame_acceleration:4d} "
          f"(vel_muneca_der = {vel_muneca_der[frame_acceleration]:.5f}, "
          f"muneca_der_y = {muneca_der_y[frame_acceleration]:.4f})")

    # ── FASE 6: CONTACT ───────────────────────────────────────────────────
    # Impacto: brazo de raqueta en su punto más alto (máxima extensión hacia
    # arriba para golpear la pelota).
    # Corrección E: en vez de buscar relativo a Acceleration (que podía estar
    # mal detectada), buscamos el MÍNIMO ABSOLUTO de muneca_der_y en la ventana
    # fija [cocking+10, cocking+150]. El análisis técnico confirmó que el mínimo
    # real (frame ~372, Y=0.349) está en esa ventana y coincide con el GT.
    # NOTA: Y mínimo = arriba en la imagen = brazo más alto = impacto.
    frame_contact = indice_minimo_local(
        muneca_der_y,
        desde=frame_cocking + 10,
        hasta=min(n, frame_cocking + 150)
    )
    fases["contact"] = frame_contact
    print(f"[Fase 6 - Contact]      frame {frame_contact:4d} "
          f"(muneca_der_y mínimo = {muneca_der_y[frame_contact]:.4f})")

    # ── FASE 7: DECELERATION ──────────────────────────────────────────────
    # El brazo de raqueta cruza hacia abajo después del impacto.
    # Señal: muneca_der Y supera el nivel del hombro der (brazo baja por
    # debajo del hombro). Si no se detecta, se usa un offset fijo acotado.
    frame_deceleration = min(frame_contact + 5, n - 1)  # fallback con cota
    buscar_hasta_decel = min(n, frame_contact + 80)
    for i in range(frame_contact + 3, buscar_hasta_decel):
        if muneca_der_y[i] > hombro_der_y[i]:
            frame_deceleration = i
            break
    fases["deceleration"] = frame_deceleration
    idx_d = min(frame_deceleration, n - 1)  # índice seguro para el print
    print(f"[Fase 7 - Deceleration] frame {frame_deceleration:4d} "
          f"(muneca_der_y = {muneca_der_y[idx_d]:.4f}, "
          f"hombro_der_y = {hombro_der_y[idx_d]:.4f})")

    # ── FASE 8: FINISH ────────────────────────────────────────────────────
    # Aterrizaje: el pie delantero (tobillo izquierdo para diestros) toca el
    # suelo y deja de bajar.
    # Corrección F: antes buscaba hasta el final del video y encontraba un
    # movimiento de acomodación tardío (frame 552). Ahora busca solo en la
    # ventana [contact+10, contact+50] (~1.3 segundos) que captura el
    # aterrizaje real justo después del impacto.
    # NOTA: Y máximo = abajo en la imagen = pie en su punto más bajo = aterrizó.
    frame_finish = indice_maximo_local(
        tobillo_izq_y,
        desde=frame_contact + 10,
        hasta=min(n, frame_contact + 50)
    )
    fases["finish"] = frame_finish
    idx_f = min(frame_finish, n - 1)  # índice seguro para el print
    print(f"[Fase 8 - Finish]       frame {frame_finish:4d} "
          f"(tobillo_izq_y máximo = {tobillo_izq_y[idx_f]:.4f})")

    print(f"\n{'='*60}")
    print("Detección completada.\n")

    # Cota de seguridad final: ningún frame puede quedar fuera de [0, n-1]
    fases = {fase: min(frame, n - 1) for fase, frame in fases.items()}

    return fases


# ─────────────────────────────────────────────
# 4. ASIGNACIÓN DE FASE A CADA FRAME
# ─────────────────────────────────────────────

def asignar_fase_por_frame(fases, n_frames):
    """
    Dado el dict de frames de inicio de cada fase, devuelve una lista de
    strings con la etiqueta de la fase asignada a cada frame.
    """
    etiquetas = ["pre_start"] * n_frames

    # Ordenar fases por frame de inicio (por si acaso)
    fases_ordenadas = sorted(fases.items(), key=lambda x: x[1])

    for idx, (fase, frame_inicio) in enumerate(fases_ordenadas):
        # La fase dura hasta el inicio de la siguiente (o hasta el final)
        if idx + 1 < len(fases_ordenadas):
            frame_fin = fases_ordenadas[idx + 1][1]
        else:
            frame_fin = n_frames

        for f in range(frame_inicio, frame_fin):
            etiquetas[f] = fase

    return etiquetas


# ─────────────────────────────────────────────
# 5. GUARDADO DEL RESULTADO
# ─────────────────────────────────────────────

def guardar_resultado(fases, ruta_json_entrada, ruta_resultados):
    """
    Guarda el dict de fases como JSON en datos/resultados/.
    Nombre del archivo: {nombre_video}_fases.json
    """
    ruta_resultados = Path(ruta_resultados)
    ruta_resultados.mkdir(parents=True, exist_ok=True)

    nombre_video = Path(ruta_json_entrada).stem.replace("_keypoints", "")
    ruta_salida = ruta_resultados / f"{nombre_video}_fases.json"

    resultado = {
        "video": nombre_video,
        "fases": {fase: {"frame": frame} for fase, frame in fases.items()}
    }

    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    print(f"Resultado guardado en: {ruta_salida}")
    return str(ruta_salida)
