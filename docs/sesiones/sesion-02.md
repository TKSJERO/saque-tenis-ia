# Sesión 02 — Hito 2: Identificación automática de fases

**Fecha:** 2026-04-14  
**Duración:** sesión única  
**Resultado:** Hito 2 COMPLETADO — 6/6 fases dentro de ±15 frames

---

## Qué se logró

- Implementado `src/fases/detector_fases.py`: detecta las 8 fases del saque
  usando señales proxy del cuerpo (sin pelota ni raqueta).
- Implementado `src/fases/visualizador_fases.py`: genera video con etiqueta
  de fase en cada frame (texto grande con borde, timestamp, rectángulo
  amarillo en transiciones).
- Implementado `detectar_fases.py` (raíz del proyecto): script principal que
  recibe JSON de keypoints, detecta fases, guarda JSON y genera video.
- Ground truth medido frame a frame en video_pro.mp4 (mejorado desde
  aproximaciones al segundo del Hito 1).
- Validación final: 6/6 fases dentro de ±15 frames (±0.5s).

**Errores finales vs ground truth revisado:**

| Fase         | GT  | Detectado | Error  |
|--------------|-----|-----------|--------|
| Start        | 5   | 5         | 0      |
| Release      | 156 | 146       | −10    |
| Cocking      | 287 | 301       | +14    |
| Acceleration | 345 | 351       | +6     |
| Contact      | 372 | 370       | −2     |
| Finish       | 394 | 398       | +4     |

---

## Decisiones técnicas tomadas

### Señales proxy del cuerpo
MediaPipe solo detecta el cuerpo. Las reglas de detección del CLAUDE.md
mencionan pelota y raqueta — se usan señales del cuerpo como proxy.
Mejora futura documentada: agregar YOLOv8 para detección de pelota/raqueta.

### Señales finales por fase
- **Start:** velocidad de `muneca_izq_y` > 0.0007 durante 6 frames (`n//4`)
- **Release:** `muneca_izq_y − torso_medio_y < −0.05` durante 5 frames
- **Loading:** `cadera_media_y` sube 0.008 sobre referencia durante 6 frames
- **Cocking:** máximo absoluto de `cadera_media_y` en ventana de carga
- **Acceleration:** velocidad de `muneca_der_y` < −0.005 durante 5 frames
- **Contact:** mínimo absoluto de `muneca_der_y` en `[cocking+10, cocking+150]`
- **Deceleration:** `muneca_der_y > hombro_der_y` (primer cruce)
- **Finish:** máximo de `tobillo_izq_y` en `[contact+10, contact+50]`

### Descubrimiento clave en los datos
La muñeca derecha (brazo de raqueta) sube continuamente desde Cocking
hasta Contact sin un "dip" visible en Y. Esto significa que el Racket Low
Point (MER) no es detectable en 2D desde vista lateral como un pico de Y.
La señal para Acceleration tuvo que cambiar a "velocidad negativa sostenida"
(inicio del swing explosivo), no "máximo de Y".

### Convención de ejes (crítica)
En MediaPipe: Y=0 es la parte superior de la imagen, Y=1 es la inferior.
"Máximo Y" = punto más bajo del cuerpo. "Mínimo Y" = punto más alto.
Documentado explícitamente al inicio de `detector_fases.py`.

---

## Estado del proyecto al cerrar

| Componente                     | Estado     |
|-------------------------------|------------|
| Entorno técnico               | COMPLETADO |
| Detección de pose (MediaPipe) | COMPLETADO |
| Identificación de fases       | COMPLETADO |
| Cálculo de ángulos articulares | PENDIENTE  |
| Comparación biomecánica        | PENDIENTE  |
| Feedback en lenguaje natural   | PENDIENTE  |
| Interfaz Streamlit             | PENDIENTE  |

**Archivos nuevos creados en esta sesión:**
- `src/fases/detector_fases.py`
- `src/fases/visualizador_fases.py`
- `detectar_fases.py`
- `datos/resultados/video_pro_fases.json`
- `videos/salida/video_pro_fases.mp4`

---

## Punto de partida exacto para la próxima sesión (Hito 3)

**Objetivo:** Calcular ángulos articulares clave en cada frame y en cada fase.

**Contexto para la IA:**
- Los ángulos a calcular están en CLAUDE.md sección "A. Parámetros biomecánicos"
- Los ángulos se calculan con 3 landmarks: punto proximal, vértice, punto distal
- Fórmula: arccos del producto punto de dos vectores normalizados
- Los ángulos deben calcularse frame a frame Y también el valor representativo
  por fase (e.g., promedio de los frames centrales de cada fase, o el valor
  en el frame de inicio de la fase).
- Input: JSON de keypoints (Hito 1) + JSON de fases (Hito 2)
- Output: JSON de ángulos en `datos/angulos/{video}_angulos.json`
- Módulo nuevo: `src/angulos/calculador_angulos.py`

**Ángulos prioritarios (los que tienen rangos biomecánicos en CLAUDE.md):**
1. Flexión de rodilla delantera (izquierda para diestros): cadera_izq–rodilla_izq–tobillo_izq
2. Flexión de rodilla trasera: cadera_der–rodilla_der–tobillo_der
3. Abducción/elevación del hombro derecho: cadera_der–hombro_der–codo_der
4. Flexión del codo derecho: hombro_der–codo_der–muneca_der
5. Inclinación del tronco: línea hombros vs horizontal

**Pregunta abierta para el Hito 3:** ¿calculamos ángulos en todos los frames
o solo en los frames de inicio de cada fase? Discutir al inicio de la sesión.
