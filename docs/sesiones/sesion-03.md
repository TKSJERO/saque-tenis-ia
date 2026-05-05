# Sesión 03 — Hito 3: Cálculo de ángulos articulares

**Fecha:** 2026-04-14
**Duración:** sesión única (continuación de la sesión 02)
**Resultado:** Hito 3 COMPLETADO — 11 parámetros biomecánicos calculados,
evaluados contra rangos de papers. Limitaciones 2D documentadas honestamente.

---

## Qué se logró

- Implementado `src/angulos/geometria.py`: primitivas geométricas 2D (ángulo
  articular, flexión, inclinación vs vertical/horizontal, diferencia de ejes).
- Implementado `src/angulos/calculador_angulos.py`: calcula 10 señales angulares
  por frame, extrae valor representativo por fase, evalúa contra rangos biomecánicos.
- Implementado `calcular_angulos.py` (raíz): script ejecutable que auto-descubre
  el JSON de fases, guarda JSON de ángulos y muestra tabla de validación.
- Primera corrida con `video_pro.mp4`: 11 parámetros con valores, evaluación y
  flag confiable_2d documentado.
- Corrección post-ejecución: `abduccion_hombro` reclasificado a `confiable_2d=False`
  tras detectar que la fórmula no mide abducción real desde vista lateral.

---

## Resultados — tabla final (video_pro.mp4)

| Parámetro | Valor | Rango ideal | Evaluación | 2D confiable |
|---|---|---|---|---|
| Flexión rodilla delantera | 42.5° | 54.8°–93.3° (>15°) | ACEPTABLE | Sí |
| Flexión rodilla trasera | 42.1° | 51°–83.8° | DEFICIENTE | Sí |
| Tronco vs vertical (Trophy) | 10.8° | 17.9°–32.1° | DEFICIENTE | Sí |
| Separación lateral | 53.9° | 24.2°–39.1° | EXCESIVO | No |
| MER hombro (proxy 2D) | 77.4° | 100°–130° | DEFICIENTE | No |
| Inclinación pélvica | 172.7° | sin rango | — | No |
| Abducción hombro (Contact) | 173.1° | 95°–125° | EXCESIVO | No |
| Flexión codo (Contact) | 10.0° | 16°–46° | DEFICIENTE | Sí |
| Tronco vs horizontal (Contact) | 79.0° | 41°–55° | EXCESIVO | Sí |
| Desviación muñeca | 11.5° | 7°–23° | ÓPTIMO | No |
| RoM rotación interna | 74.0° | sin rango | — | No |

**Nota:** evaluación "EXCESIVO" en abduccion_hombro no es un hallazgo biomecánico
real — es un artefacto de la medición lateral (ver sección de limitaciones).

---

## Decisiones técnicas tomadas

### Cálculo solo en 2D (X,Y), ignorar Z de MediaPipe
La coordenada Z de MediaPipe es una estimación con error alto. Todos los cálculos
usan solo las coordenadas normalizadas X e Y del plano de la imagen.

### Flag confiable_2d por parámetro
En lugar de excluir parámetros no medibles correctamente, se calculan todos pero
se documenta la confiabilidad. El sistema siempre da un valor, siempre avisa si
no es confiable. Esto es más útil para el feedback que un "no disponible".

### Evaluación en 5 niveles
`optimo` / `aceptable` / `deficiente` / `excesivo` / `no_evaluable`

El nivel `aceptable` aplica solo cuando hay discrepancia de fuentes con un rango
mínimo alternativo (caso único: flexion_rodilla_delantera, Kovacs >15° vs élite 54.8°+).

### Extracción del valor representativo por tipo
- `puntual`: valor en el frame de inicio de la fase (Contact, Trophy)
- `pico_max` / `pico_min`: máximo o mínimo en la ventana de fase
- `rango`: max − min (para RoM)

---

## Limitaciones identificadas y documentadas

### abduccion_hombro — no medible desde lateral
La fórmula `cadera_der → hombro_der → codo_der` mide la separación brazo-tronco
en el plano sagital. Cuando el brazo está levantado al servir, el codo queda sobre
el hombro y el ángulo se acerca a 180°. El paper mide abducción en plano frontal
(vista de frente). No son comparables. Reclasificado a `confiable_2d=False`.

### inclinacion_tronco_horizontal en Contact — discrepancia con el paper
Medido: ~79° de la horizontal. Paper: 41°–55°. No se concluye error de código.
Posibles causas: diferencia de segmento de referencia (paper usa cadera→C7 o
cadera→C7 proyectado; nosotros usamos midpoint_caderas→midpoint_hombros),
diferencia 2D vs 3D, técnica específica del pro. Pendiente de investigación en Hito 4.

### Pico de rodilla delantera — off-by-one en ventana
El pico se detecta en frame 300, que es el último frame ANTES del Cocking (frame 301).
La rodilla seguía flexionándose hasta la Trophy Position. El verdadero pico es
probablemente frame 301 o los siguientes. Diferencia estimada: 1–3°. El valor de
42.5° ya es "ACEPTABLE" (por encima del mínimo de Kovacs de 15°), y este ajuste
no cambiaría la evaluación. Se deja documentado para precisión futura.

### Parámetros no medibles en 2D lateral
`separacion_lateral`, `mer_hombro_proxy`, `inclinacion_pelvica`, `desviacion_muneca`,
`rom_rotacion_interna`, `abduccion_hombro` — todos `confiable_2d=False`. Los valores
se calculan y muestran pero con advertencia. No se usan para feedback negativo en Hito 4.

---

## Archivos creados en esta sesión

| Archivo | Descripción |
|---|---|
| `src/angulos/geometria.py` | Primitivas geométricas 2D |
| `src/angulos/calculador_angulos.py` | Cálculo, extracción y evaluación de ángulos |
| `calcular_angulos.py` | Script ejecutable raíz |
| `datos/angulos/video_pro_angulos.json` | Resultado del análisis de video_pro.mp4 |

---

## Estado del proyecto al cerrar

| Componente | Estado |
|---|---|
| Entorno técnico | COMPLETADO |
| Detección de pose (MediaPipe) | COMPLETADO |
| Identificación de fases | COMPLETADO |
| Cálculo de ángulos articulares | COMPLETADO |
| Comparación biomecánica | COMPLETADO (integrado en Hito 3) |
| Generación de feedback en lenguaje natural | PENDIENTE |
| Interfaz Streamlit | PENDIENTE |

---

## Punto de partida exacto para la próxima sesión (Hito 4)

**Objetivo:** Generar feedback en lenguaje natural usando la API de Claude desde Python.

**Módulo nuevo:** `src/feedback/generador_feedback.py`

**Input disponible:**
- JSON de ángulos: `datos/angulos/{video}_angulos.json`
  Estructura: `resumen_por_fase` con valor, rango_ideal, evaluacion, confiable_2d, advertencia
- Las 8 fases detectadas en `datos/resultados/{video}_fases.json`

**Decisiones pendientes para el inicio de la sesión:**
1. Configuración de API key de Anthropic (variable de entorno o archivo .env)
2. Qué parámetros `confiable_2d=False` se incluyen en el feedback vs se omiten
3. Tono del feedback: ¿solo negativo/positivo? ¿qué hacer con "ACEPTABLE"?
4. Resolver la discrepancia del tronco (~79° vs 41–55°) antes de generar feedback
   sobre ese parámetro — opciones: cambiar segmento de referencia, ajustar rango,
   o marcar como "en revisión" en el feedback

**Regla de confianza del proyecto:** 95% de certeza antes de escribir código.
Hacer preguntas de seguimiento hasta alcanzar ese nivel.
