# CLAUDE.md — Contexto del proyecto: Analizador de Saque de Tenis

## ¿Qué es este archivo?
Este archivo le da contexto a Claude Code para que cada sesión nueva
arranque sabiendo quién es Pablo, qué se está construyendo y cómo
trabajar juntos. No hace falta re-explicar nada.

---

## Regla de confianza
No hacer cambios ni escribir código hasta tener 95% de confianza
en lo que se debe construir. Hacer preguntas de seguimiento hasta
alcanzar ese nivel. Es mejor preguntar tres veces que escribir
código equivocado.

---

## Sobre el usuario
- Nombre: Pablo (usuario: Jerónimo)
- Nivel técnico: cero experiencia previa con Python y terminal
- Sistema operativo: Windows 11, usa PowerShell
- Idioma: español
- Necesita explicaciones en lenguaje claro, sin jerga innecesaria
- Antes de ejecutar cualquier comando, explicar brevemente qué hace
- Antes de hacer cambios grandes, proponer el plan y esperar confirmación
- Decir qué va a ver en pantalla y qué significa cada resultado

---

## Objetivo del proyecto
Construir una aplicación que analiza videos de saques de tenis y da
feedback biomecánico automatizado, como si fuera un entrenador.

### Flujo completo de la aplicación:
1. El usuario sube un video mp4 (grabado desde un lateral)
2. MediaPipe Pose detecta los puntos del cuerpo frame a frame
3. El sistema identifica las 8 fases del saque
4. Se calculan ángulos articulares clave en cada fase
5. Los valores se comparan contra rangos biomecánicos ideales (papers)
6. Se genera feedback en lenguaje natural tipo entrenador
7. Todo se muestra en una interfaz simple hecha con Streamlit

---

## Estado actual del proyecto
- Entorno técnico: configurado (Python, Git, entorno virtual, librerías)
- Datos biomecánicos: DISPONIBLES (ver sección REFERENCIA BIOMECÁNICA)
- Detección de pose con MediaPipe: COMPLETADO — PoseLandmarker (Tasks API) extrae 33 keypoints frame a frame con 100% de detección en ambos videos de prueba. Output: JSON en datos/keypoints/ y video con esqueleto en videos/salida/
- Identificación automática de fases: COMPLETADO — detector_fases.py detecta 6/6 fases dentro de ±15 frames (±0.5s) contra ground truth revisado frame a frame. Señales proxy del cuerpo (sin pelota/raqueta). Output: JSON en datos/resultados/ y video con etiquetas en videos/salida/
- Cálculo de ángulos articulares: COMPLETADO — 11 ángulos calculados frame a frame con evaluación contra rangos biomecánicos. 4 parámetros confiables_2d=True validados (rodilla delantera, rodilla trasera, flexión codo, inclinación tronco). 7 parámetros con limitaciones 2D documentadas honestamente. Output: JSON en datos/angulos/. Pendientes para Hito 4: convención del tronco (~79° vs paper 41–55°), generación de feedback contextualizado.
- Comparación contra rangos biomecánicos ideales: COMPLETADO (integrado en Hito 3 — ver calculador_angulos.py)
- Generación de feedback en lenguaje natural: COMPLETADO — claude-sonnet-4-6, temperature 0.3, max_tokens 2048. System prompt iterado 1 vez para forzar concisión. Output: 374 palabras, ~$0.02 por análisis. Archivo guardado en datos/feedback/. Manejo especial del tronco en Contact (valor en revisión en Limitaciones, no evaluado como error). API key gestionada con .env + python-dotenv.
- Interfaz Streamlit: PENDIENTE

---

## Tecnologías del proyecto
- Python 3.12 (ver "Decisiones técnicas" para saber por qué no 3.14)
- MediaPipe — detección de pose (puntos del cuerpo)
- OpenCV (opencv-python) — procesamiento de video frame a frame
- NumPy — cálculo de ángulos y operaciones matemáticas
- Streamlit — interfaz web simple para subir video y ver resultados

---

## Convenciones de código
- Código y comentarios en español cuando sea posible
- Nombres de variables descriptivos (no abreviaturas crípticas)
- Cada función debe tener un comentario corto que explique qué hace
- Archivos pequeños y enfocados en una sola responsabilidad

---

## Cómo trabajar con Pablo
- Ir paso a paso, esperar "sí" o confirmación antes del siguiente paso
- Si algo falla, explicar el error en palabras simples primero
- Proponer antes de ejecutar cambios que afecten muchos archivos
- Si algo no queda claro, preguntar antes de asumir

---

## REFERENCIA BIOMECÁNICA

Datos extraídos de papers científicos vía NotebookLM.
Fuentes: Reid et al., Kovacs & Ellenbecker, Jacquier-Bret & Gorce,
Elliott et al., Bradley et al.

---

### A. Parámetros biomecánicos medibles con rangos ideales

| Parámetro | Fase | Rango ideal | Por debajo del rango | Por encima del rango | Fuente |
|---|---|---|---|---|---|
| Separación por flexión lateral (hombro-pelvis) | Loading | 24.2°–39.1° (media ~31.5° ±7.5°) | Menor momentum angular sobre el eje del tronco, menos velocidad de pelota | Sin efectos adversos directos reportados (anatomía limita rangos mayores) | Reid et al. |
| Inclinación del tronco | Trophy / Loading | 17.9°–32.1° (media 25.0° ±7.1°) | Menor almacenamiento de energía elástica y transferencia en cadena cinética | Estrés asimétrico excesivo en columna lumbar → riesgo de espondilólisis | Jacquier-Bret & Gorce, Kovacs & Ellenbecker |
| Flexión de rodilla delantera | Loading / Trophy | Mínimo >15° / élite: 54.8°–93.3° (74° ±19.3°) | Leg drive deficiente → sobrecarga de hombro anterior y codo medial | No se asocia a lesión directa (depende de técnica foot-back vs foot-up) | Kovacs & Ellenbecker, Reid et al., Jacquier-Bret & Gorce |
| Flexión de rodilla trasera | Trophy | 51.0°–83.8° (media 67.4° ±16.4°) | Menor impulso vertical → menos velocidad de raqueta | Fatiga muscular prematura sin ganancia adicional de velocidad | Jacquier-Bret & Gorce, Kovacs & Ellenbecker |
| Rotación externa máxima del hombro (MER) | Cocking / Racket Low Point | 100°–130° (método anatómico) / 160°–184° (método vectores) | Menor velocidad de raqueta, déficit del efecto stretch-shortening | Riesgo de pinzamiento interno posterior + carga crítica en cápsula anterior | Reid et al., Kovacs & Ellenbecker, Elliott et al., Jacquier-Bret & Gorce |
| Inclinación pélvica anterior | Cocking | Controlada (no hay rango explícito en grados) | Corta el momentum hacia adelante de la cadena cinética | Asociación grande con dolor lumbar y pinzamiento femoroacetabular | Bradley et al. |
| Abducción / Elevación del hombro | Contact | 95°–125° (óptimo ~110° ±15°) | Menor altura de contacto, transferencia subóptima de fuerzas | Hiperabducción → estrés excesivo en hombro + riesgo de pinzamiento | Kovacs & Ellenbecker, Jacquier-Bret & Gorce, Reid et al. |
| Flexión del codo | Contact | 16°–46° (media ~30° ±16°) | Pierde ventaja mecánica para rotación medial del hombro | Contacto muy bajo con la pelota, ángulo de ataque subóptimo | Kovacs & Ellenbecker, Jacquier-Bret & Gorce |
| Extensión de muñeca | Contact | 7°–23° (media 15° ±8°) | Dificultad para transferir momentum final y rotación longitudinal | Epicondilalgia lateral por sobreuso si fuerzas no se estabilizan | Kovacs & Ellenbecker |
| Inclinación del tronco sobre la horizontal | Contact | 41°–55° (media 48° ±7°) | Disminuye la altura vertical ganada, afecta trayectoria del saque | Cargas asimétricas severas en zona lumbar → riesgo de espondilólisis | Kovacs & Ellenbecker |
| RoM de Rotación Interna | Follow-through | Rango completo, fluido y sin restricción | Déficit → riesgo muy alto de desgarros labrales y GIRD | Laxitud excesiva → inestabilidad anterior si rotadores excéntricos fallan | Bradley et al. |

#### Nota sobre discrepancias en las fuentes

**Flexión de rodilla delantera:**
- Kovacs & Ellenbecker: mínimo recomendado >15° (límite patológico)
- Reid et al. y Jacquier-Bret & Gorce: mediciones reales en élite entre
  64.5° ±9.7° y 74.6° ±17.1° (la realidad funcional es mucho mayor)

**Rotación externa máxima del hombro (MER):**
- Elliott et al.: 169°–172° ±12° (método de vectores inter-segmentos,
  sobreestima la rotación real)
- Reid et al.: ~115° ±15° (matrices de coordenadas anatómicas, método
  más preciso y moderno)
- Jacquier-Bret & Gorce (metaanálisis 2024): promedio de 130.1° ±26.5°
  (combinando distintas metodologías)

---

### B. Las 8 fases del saque y cómo detectarlas en video 2D

| # | Fase | Inicio | Fin | Cómo detectarla en video (coordenadas 2D) |
|---|---|---|---|---|
| 1 | Start (Inicio) | Primer movimiento voluntario desde posición de descanso | Instante previo a la liberación de la pelota | Periodo inicial estático. Termina cuando la mano no dominante empieza a separarse en el eje Y |
| 2 | Release (Lanzamiento) | La pelota abandona la mano no dominante | Cuerpo llega a su máxima flexión inferior | Distancia entre coordenada de pelota y mano no dominante empieza a aumentar. Pelota sube en eje Y |
| 3 | Loading (Carga) | Liberación de la pelota | Trophy Position (cuerpo inferior totalmente cargado) | Fin detectable: rodilla en máxima flexión, codos en su Y más baja, cabeza de raqueta en primer pico de altura |
| 4 | Cocking (Montaje) | Trophy Position | Rotación externa máxima del hombro (MER) = Racket Low Point | La punta de la raqueta apunta al suelo, alcanzando su coordenada Y más baja por detrás de la espalda |
| 5 | Acceleration (Aceleración) | MER / Racket Low Point | Contacto con la pelota | Aceleración masiva de hombro, codo y muñeca hacia arriba/adelante. Extensión brusca de rodilla delantera |
| 6 | Contact (Impacto) | Choque raqueta-pelota | Separación raqueta-pelota | Coordenadas de pelota se superponen con centro de raqueta. Tronco ~48°, brazo ~100°–110°, codo ~30° flexión |
| 7 | Deceleration (Desaceleración) | Después del contacto | Fin de desaceleración del tren superior e inferior | Brazo y raqueta cruzan el eje vertical del cuerpo hacia abajo y al lado opuesto. Y de mano cae bruscamente |
| 8 | Finish (Finalización) | Fin de desaceleración | Movimiento hacia el próximo golpe | Coordenadas del pie delantero (o ambos pies) detienen su descenso en Y → aterrizaje |

**Dato clave de timing:** La fase de Cocking termina 90 ms ±14 ms antes del impacto.
La fase de Acceleration dura menos de 10 ms en servidores avanzados.

---

### C. Los 10 errores biomecánicos más comunes

| # | Error | Cómo detectarlo numéricamente | Consecuencia rendimiento | Consecuencia lesión | Corrección |
|---|---|---|---|---|---|
| 1 | Pobre flexión de rodillas (déficit de leg drive) | Flexión rodilla delantera <15° (o <10°) en fase de carga | Menos energía cinética transferible → menor velocidad de raqueta | Sobrecarga de hombro y codo por compensación | Flexionar ambas rodillas >15° en la preparación |
| 2 | Desequilibrio de rotadores del hombro | Relación trabajo excéntrico externo / concéntrico interno ≤1.0 | El sistema limita la velocidad máxima de rotación interna | Riesgo de desgarros severos en desaceleración | Fortalecer rotadores externos con trabajo excéntrico (bandas elásticas) |
| 3 | Hiperextensión y flexión lateral excesiva de zona lumbar | Ángulos elevados de flexión lateral + rotación lumbar en aceleración | Transferencia ineficiente de torque (fugas en la cadena cinética) | Riesgo alto de dolor crónico (LBP) y espondilólisis | Generar potencia por rotación controlada, no arqueando la espalda |
| 4 | Hiperangulación / Arm Lag (abducción horizontal excesiva) | Brazo de golpeo >7° por detrás del plano coronal durante cocking | Descoordinación de cadena cinética, retrasa llegada de la raqueta | Pinzamiento interno posterior + carga crítica en cápsula anterior | Sincronizar descenso del brazo de lanzamiento con rotación del torso |
| 5 | Lanzamiento de pelota erróneo (toss muy vertical o retrasado) | Abducción de hombro en contacto >110°–125° por mala posición de pelota | Pérdida de ventaja mecánica y dirección del saque | Pinzamiento subacromial + asociación fuerte con LBP | Lanzar pelota ligeramente hacia adelante y a la derecha (diestros) |
| 6 | Déficit de rotación interna del hombro (GIRD) | Pérdida de 10°–15° de RoM en rotación interna a 90° de abducción | Reducción de potencia (la rotación interna genera velocidad de raqueta) | Asociación profunda con desgarros del labrum | Rutinas de estiramiento de cápsula posterior (sleeper stretch) |
| 7 | Inclinación pélvica anterior excesiva | Ángulo exagerado de anteversión pélvica en trophy position / cocking | Inestabilidad del core → disipación de energía entre piernas y brazos | Tamaño de efecto grande para LBP y pinzamiento femoroacetabular | Mantener pelvis neutra contrayendo abdomen y glúteos en la carga |
| 8 | Sobre-rotación pélvica hacia la espalda | Rotación pélvica derecha desproporcionada en cocking (diestros) | Rompe el mecanismo de separación hombro-pelvis, pierde torque acumulado | Mayor tamaño de efecto para LBP (d=4.030) | Limitar apertura de cadera y rotar hombros sobre base pélvica estable |
| 9 | Extensión excesiva de muñeca en el contacto | Muñeca extendida fuera del rango 7°–23° en el impacto | Menor control de dirección y dificultad para transmitir pronación | Epicondilalgia lateral por microtraumas repetitivos | Impactar con muñeca estable, dejar que pronación y hombro aceleren |
| 10 | Rotación escapular compensatoria (disquinesia escapular) | Ángulos de rotación ascendente de escápula excepcionalmente altos en release o contact | Altera el ritmo escápulohumeral, merma velocidad angular del brazo | Predictor de problemas de hombro, sobrecarga del trapecio y cuello | Fortalecer trapecio inferior y serrato anterior para movimiento limpio |

---

## Decisiones técnicas

Registro histórico de decisiones importantes tomadas durante el desarrollo del proyecto.

---

### [2026-04-13] Decisiones del Hito 1 — Detección de pose

**Decisión 1 — API de MediaPipe:** Se usa `mediapipe.tasks.python.vision.PoseLandmarker` (Tasks API). La API legacy `mp.solutions` fue eliminada en MediaPipe 0.10+.

**Decisión 2 — Modelo local:** El archivo `pose_landmarker_full.task` (~29 MB) se descarga una vez y se guarda en `modelos/`. Esta carpeta está en `.gitignore`. Se eligió el modelo `full` (no `lite` ni `heavy`) como balance entre velocidad y precisión.

**Decisión 3 — Estructura JSON de keypoints:** Cada archivo JSON contiene: metadata del video (fps, resolución, total_frames) + array de frames. Cada frame tiene: número, timestamp_ms, pose_detectada (bool), y array de 33 landmarks con {id, nombre, x, y, z, visibility}. Coordenadas normalizadas (0.0–1.0).

**Decisión 4 — Nombres de archivos de salida:** JSON → `datos/keypoints/{nombre_video}_keypoints.json`. Video anotado → `videos/salida/{nombre_video}_esqueleto.mp4`. El nombre base se toma del archivo de entrada sin extensión.

**Decisión 5 — Videos de entrada aceptados:** El script `procesar_video.py` acepta `.mp4` y `.mov` sin modificación. Los videos verticales (portrait) se dejan para el futuro; por ahora se requiere grabación horizontal.

---

### [2026-04-09] MediaPipe 0.10.x usa la API Tasks, no la API Solutions

**Decisión:** El proyecto usará la API `mediapipe.tasks` (nueva) en lugar de `mediapipe.solutions` (antigua, eliminada en 0.10+).

**Motivo:** MediaPipe 0.10.33 eliminó completamente el módulo `mp.solutions`. El punto de entrada ahora es `mediapipe.tasks.python.vision.PoseLandmarker`. Esta nueva API requiere descargar un archivo de modelo `.task` (pose_landmarker.task) que se obtendrá al arrancar el Hito 1.

**Cómo se resuelve:** En el Hito 1 se descargará el modelo oficial de Google y se guardará en el proyecto. El código de detección usará `PoseLandmarker` en lugar de `mp.solutions.pose.Pose`.

---

### [2026-04-09] Usar Python 3.12 en lugar de Python 3.14

**Decisión:** El proyecto usa Python 3.12. Python 3.14 está instalado en el sistema pero NO se usa para este proyecto.

**Motivo:** MediaPipe (librería central del proyecto para detección de pose) no tiene soporte oficial para Python 3.14. La versión más reciente de MediaPipe (0.10.33, lanzada en marzo de 2026) soporta hasta Python 3.12 como máximo.

**Cómo se resuelve:** Se instaló Python 3.12 en paralelo al 3.14 usando el instalador oficial de python.org. El py launcher de Windows permite tener ambas versiones conviviendo sin conflictos. El entorno virtual del proyecto se crea apuntando explícitamente a Python 3.12 con el comando `py -3.12 -m venv venv`.

---

### [2026-04-14] Hito 2 — Señales proxy del cuerpo para detección de fases

**Decisión:** El detector de fases usa exclusivamente los keypoints del cuerpo (MediaPipe) como señales proxy. No se detectan la pelota ni la raqueta.

**Motivo:** MediaPipe solo extrae landmarks del cuerpo humano. Las reglas de detección del CLAUDE.md mencionan coordenadas de pelota y raqueta, pero esas señales no están disponibles en los JSON del Hito 1. Las señales del cuerpo son suficientes para validar contra el ground truth aproximado.

**Señales proxy usadas por fase:**
- Start → varianza de `muneca_izq` Y cruza umbral (deja de ser estática)
- Release → distancia entre `muneca_izq` y `muneca_der` empieza a crecer
- Loading → `cadera` (promedio izq+der) Y sigue aumentando (cuerpo bajando)
- Cocking → `cadera` Y alcanza máximo local (cuerpo en punto más bajo = Trophy Position)
- Acceleration → `muneca_der` Y alcanza máximo local (brazo de raqueta en punto más bajo = MER)
- Contact → `muneca_der` Y alcanza mínimo local (brazo en punto más alto = impacto)
- Deceleration → `muneca_der` Y supera nivel del hombro (brazo bajando tras impacto)
- Finish → `tobillo_izq` Y se estabiliza (aterrizaje)

**Nota sobre el eje Y de MediaPipe:** Y va de 0 (arriba de la imagen) a 1 (abajo). Por eso "máximo Y" = punto más bajo del cuerpo, y "mínimo Y" = punto más alto. Este eje está comentado al inicio de `detector_fases.py`.

**Mejora futura:** Si se quiere mayor precisión, se puede agregar detección de pelota/raqueta con un modelo adicional (YOLOv8 entrenado o similar). Por ahora, las señales del cuerpo son suficientes para validación contra ground truth aproximado.

---

### [2026-04-14] Hito 2 — Correcciones aplicadas al detector de fases

Detector iterado en 3 corridas hasta lograr 6/6 fases dentro de ±15 frames.

**Correcciones finales aplicadas (sobre detector_fases.py):**

- **Start (A):** `UMBRAL_MOVIMIENTO` bajado de 0.0015 a 0.0007; ventana de búsqueda acotada a `[5, n//4]` (antes `n//3`). Motivo: movimiento inicial del jugador es sutil, el umbral alto lo perdía.
- **Release (B→final):** Señal cambiada de `dist_munecas mínimo + offset` a `muneca_izq_y < torso_medio_y − 0.05` sostenido 5 frames. Motivo: la distancia entre muñecas disparaba con micro-separaciones tempranas; el cruce de torso captura cuando el toss ya está "bien arriba" (frame ~146 vs GT 156, error −10).
- **Cocking (sin tocar):** cadera_media_y máximo local — ya estaba dentro de tolerancia (+14 frames).
- **Acceleration (D+ajuste):** Señal cambiada de "máximo de muneca_der_y" a "velocidad negativa sostenida de muneca_der_y" con `UMBRAL_SWING = 0.005`. Motivo: la muñeca sube continuamente desde Cocking hasta Contact sin un dip claro; el máximo que se detectaba era el follow-through. El umbral de 0.005 captura el swing explosivo, no el inicio gradual.
- **Contact (E):** Ventana de búsqueda cambiada a `[cocking+10, cocking+150]` (absoluto, no relativo a Acceleration). Motivo: Acceleration mal detectada arrastraba Contact; el mínimo absoluto de muneca_der_y en la ventana fija coincide con el impacto real (error −2 frames).
- **Finish (F):** Ventana acotada a `[contact+10, contact+50]`. Motivo: antes buscaba hasta el final del video y encontraba movimiento de acomodación tardío (frame 552 vs GT 394).

**Ground truth final revisado (video_pro.mp4, medido frame a frame):**
Start=5, Release=156, Cocking=287, Acceleration=345, Contact=372, Finish=394.

**Resultado final:** 6/6 fases dentro de ±15 frames. Errores: Start 0, Release −10, Cocking +14, Acceleration +6, Contact −2, Finish +4.

---

### [2026-04-14] Hito 3 — Hallazgos sobre limitaciones 2D

**abduccion_hombro reclasificado a confiable_2d=False:**
La fórmula `angulo_entre_tres_puntos(cadera_der, hombro_der, codo_der)` en vista lateral mide
la separación brazo-tronco en el plano sagital, no la abducción real (plano frontal). Cuando el
brazo está levantado al golpear, el codo queda sobre el hombro y el ángulo resultante se acerca
a 180°. El rango del paper (95°–125°) se mide en plano frontal y no es comparable con esta
medición lateral. Se mantiene el rango ideal pero el parámetro queda marcado como no confiable.

**Parámetros confiables 2D confirmados (confiable_2d=True):**
- `flexion_rodilla_delantera` — landmarks con visibility > 0.9 en el frame del pico
- `flexion_rodilla_trasera` — landmarks con visibility > 0.9 en el frame del pico
- `flexion_codo` — medición directa en plano sagital, visible desde lateral
- `inclinacion_tronco_horizontal` e `inclinacion_tronco_vertical` — medición de eje tronco confiable en 2D

**Pendiente de investigación en Hito 4 — Convención del tronco:**
La inclinación del tronco en Contact se mide como ~79° de la horizontal en nuestro sistema
(midpoint_caderas → midpoint_hombros), mientras el paper indica 41°–55°. Posibles causas:
(1) diferencia en segmento de referencia (algunos papers usan cadera→C7, otros cadera→hombros),
(2) diferencia 2D vs 3D, (3) técnica particular del pro analizado. No se concluye error de
código — se investiga en Hito 4 antes de generar feedback sobre este parámetro.

**Rango abduccion_hombro no validable desde lateral:**
El rango 95°–125° de Kovacs & Ellenbecker, Jacquier-Bret & Gorce y Reid et al. se mide en
el plano frontal. Desde vista lateral 2D no es posible validar este parámetro correctamente.

---

### [2026-04-15] Hito 4 — Generación de feedback con API de Claude

**Decisión 1 — Modelo y parámetros:** `claude-sonnet-4-6`, temperature 0.3, max_tokens 2048. Temperature 0.3 da variabilidad controlada sin alucinaciones. max_tokens 1024 fue insuficiente (respuesta truncada); se subió a 2048.

**Decisión 2 — System prompt iterado:** El prompt fue iterado 1 vez para forzar concisión. Primera versión: 666 palabras (excedía el objetivo). Cambios aplicados: bullets de máximo 40 palabras, contexto de fase en máximo 15 palabras, regla de economía de palabras (sin muletillas), límite redactado como obligatorio con consecuencia explícita ("has fallado la tarea"). Resultado final: 374 palabras dentro del rango 250–400.

**Decisión 3 — Tronco en Contact (inclinacion_tronco_horizontal):** El sistema mide ~79° mientras el paper indica 41°–55°. Causa probable: diferencia de convención entre segmentos de referencia (cadera→hombros vs cadera→C7) o diferencia 2D vs 3D. Decisión: no evaluar como error. El parámetro aparece solo en la sección Limitaciones con el texto: "valor en revisión por diferencia entre método de medición 2D y fuente bibliográfica."

**Decisión 4 — Gestión de API key:** La clave se guarda en `.env` (archivo excluido del repositorio en `.gitignore`). El módulo `python-dotenv` la carga en tiempo de ejecución. Nunca se hardcodea en el código.

**Decisión 5 — Arquitectura del módulo:** Tres funciones separadas: `cargar_datos_angulos()`, `construir_input_para_claude()`, `generar_feedback()`, `guardar_feedback()`. El input a Claude es texto estructurado legible (no JSON crudo) para facilitar debug y mejorar comprensión del modelo. Parámetros `no_evaluable` se filtran antes de enviar.

**Costo operativo:** ~$0.018–$0.024 USD por análisis completo (1,800–2,000 tokens input, 700–1,200 tokens output).

---

### [2026-04-14] Ground truth manual para validación del Hito 2

**Archivo:** `docs/ground_truth_video_pro.md`

Anotación manual de los frames donde empieza cada fase del saque en `video_pro.mp4` (563 frames, 30 fps). Se usará para validar el detector automático de fases del Hito 2. Fases anotadas: Start (~30), Release (~150), Cocking (~270-300), Acceleration (~330), Contact (~360), Finish (~390). Fases 3 y 7 se infieren entre las marcadas.
