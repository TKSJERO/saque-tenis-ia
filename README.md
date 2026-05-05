# Analizador de Saque de Tenis con IA

Aplicación que analiza videos de saques de tenis y genera feedback 
biomecánico automático, como si fuera un entrenador. Usa visión 
por computadora para detectar los puntos del cuerpo frame a frame, 
mide ángulos articulares clave en cada fase del movimiento, y los 
compara contra rangos ideales extraídos de papers científicos.

---

## Estado actual del proyecto

| Componente | Estado |
|---|---|
| Entorno técnico (Python 3.12, librerías) | Listo |
| Estructura de carpetas y arquitectura | Lista |
| Referencia biomecánica (papers) | Lista |
| Detección de pose con MediaPipe | Pendiente |
| Identificación automática de fases | Pendiente |
| Cálculo de ángulos articulares | Pendiente |
| Comparación contra rangos ideales | Pendiente |
| Generación de feedback en lenguaje natural | Pendiente |
| Interfaz Streamlit | Pendiente |

> El proyecto está en fase de setup inicial. La base técnica está 
> armada y los datos biomecánicos de referencia están disponibles. 
> El código del analizador se construirá en las próximas sesiones.

---

## Tecnologías

| Librería | Para qué se usa |
|---|---|
| **MediaPipe Pose** | Detecta 33 puntos del cuerpo (keypoints) en cada frame del video |
| **OpenCV** | Lee el video frame a frame y dibuja el esqueleto encima |
| **NumPy** | Calcula ángulos entre articulaciones a partir de coordenadas |
| **Streamlit** | Genera la interfaz web donde el usuario sube el video y ve los resultados |

---

## Requisitos del sistema

- Windows 10 u 11 (64-bit)
- Python 3.12 instalado desde [python.org](https://www.python.org/downloads/)
  - Python 3.13 y 3.14 **no son compatibles** con MediaPipe
- Git for Windows instalado desde [git-scm.com](https://git-scm.com/)
- Al menos 4 GB de RAM recomendados
- El video a analizar debe ser un archivo `.mp4` grabado desde un lateral

---

## Instalación

Sigue estos pasos en orden. Abre PowerShell en la carpeta del proyecto.

**1. Obtener el proyecto**

Por ahora el proyecto vive localmente. Si lo tienes en tu computadora, 
abre PowerShell dentro de la carpeta `saque-tenis-ia`. Más adelante, 
cuando el proyecto se suba a GitHub, este paso se reemplazará por un 
`git clone`.

**2. Crear el entorno virtual apuntando a Python 3.12**
```bash
py -3.12 -m venv venv
```

**3. Activar el entorno virtual**
```bash
venv\Scripts\activate
```
Verás `(venv)` al inicio de la línea en la terminal. Eso confirma 
que el entorno está activo.

**4. Instalar las librerías**
```bash
pip install -r requirements.txt
```

**5. Verificar que todo está bien instalado**
```bash
python verificar_instalacion.py
```
Si todo está correcto, verás un mensaje confirmando las versiones 
de cada librería.

---

## Cómo usar (flujo previsto)

> Esta sección describe el flujo que tendrá la aplicación cuando esté 
> completa. Todavía no está implementada.

**1. Iniciar la aplicación**
```bash
streamlit run src/interfaz/app.py
```
Se abrirá automáticamente en el navegador en `http://localhost:8501`.

**2. Subir un video**
- El usuario sube un archivo `.mp4` desde la interfaz
- Recomendado: grabado desde un lateral, con el jugador completamente 
  visible durante todo el saque

**3. Procesamiento automático**
El sistema realiza los siguientes pasos sin intervención del usuario:
1. Extrae los keypoints del cuerpo en cada frame con MediaPipe
2. Identifica las 8 fases del saque (Start → Finish)
3. Calcula los ángulos articulares clave en cada fase
4. Compara los valores medidos contra los rangos biomecánicos ideales

**4. Resultados y feedback**
La aplicación muestra:
- El video original con el esqueleto dibujado encima
- Una tabla con los ángulos medidos versus los rangos ideales
- Feedback en lenguaje natural por cada parámetro fuera de rango
- Ejemplo: *"Tu flexión de rodilla es insuficiente en la fase de carga. 
  Medimos 8°, el rango ideal es mayor a 15°. Estás perdiendo potencia 
  en el leg drive y sobrecargando el hombro como compensación."*

---

## Estructura del proyecto

```
saque-tenis-ia/
│
├── src/                  ← Código fuente del analizador
│   ├── deteccion/        ← Extracción de keypoints con MediaPipe
│   ├── fases/            ← Identificación de las 8 fases del saque
│   ├── angulos/          ← Cálculo de ángulos articulares
│   ├── analisis/         ← Comparación contra rangos biomecánicos
│   ├── feedback/         ← Generación de texto de feedback
│   └── interfaz/         ← App Streamlit (interfaz de usuario)
│
├── videos/
│   ├── entrada/          ← Videos originales del usuario
│   ├── salida/           ← Videos procesados con esqueleto
│   └── prueba/           ← Videos de desarrollo (no se suben a Git)
│       ├── pros/         ← Videos de referencia de jugadores profesionales
│       └── propios/      ← Videos propios para testeo
│
├── datos/
│   ├── keypoints/        ← JSONs con keypoints extraídos (caché por video)
│   └── resultados/       ← JSONs con resultados del análisis biomecánico
│
├── notebooks/            ← Exploración y prototipado en Jupyter
├── tests/                ← Tests automáticos por módulo
├── docs/                 ← Documentación adicional
│
├── CLAUDE.md             ← Contexto del proyecto para Claude Code
├── requirements.txt      ← Librerías necesarias
├── .gitignore            ← Excluye videos y datos pesados de Git
└── verificar_instalacion.py ← Script de prueba de humo
```

---

## Roadmap

### Hito 1 — Detección de pose (próxima sesión)
- Leer un video mp4 con OpenCV
- Extraer los keypoints con MediaPipe Pose
- Guardar los keypoints en un JSON en `datos/keypoints/`
- Dibujar el esqueleto sobre el video y guardarlo en `videos/salida/`

### Hito 2 — Identificación de fases
- Implementar las reglas de detección para las 8 fases del saque
- Etiquetar cada frame con su fase correspondiente
- Validar con videos de prueba de jugadores profesionales

### Hito 3 — Cálculo de ángulos y análisis biomecánico
- Calcular los 11 ángulos articulares definidos en la referencia biomecánica
- Comparar cada ángulo medido contra su rango ideal por fase
- Generar un reporte estructurado por video (qué está bien, qué no)

### Hito 4 — Feedback en lenguaje natural
- Traducir los resultados numéricos en texto comprensible
- Priorizar los errores más impactantes
- Incluir la corrección recomendada para cada error detectado

### Hito 5 — Interfaz Streamlit
- Subida de video desde el navegador
- Visualización del video procesado con esqueleto
- Tabla de ángulos medidos vs. ideales
- Sección de feedback final

---

## Créditos y fuentes biomecánicas

Los rangos biomecánicos ideales, las reglas de detección de fases y 
los errores comunes utilizados en este proyecto provienen de la 
siguiente literatura científica:

- **Reid, M. et al.** — Cinemática del saque de tenis, método de 
  coordenadas anatómicas para el hombro
- **Kovacs, M. & Ellenbecker, T.** — Biomecánica del saque y 
  prevención de lesiones en tenis
- **Jacquier-Bret, J. & Gorce, P.** — Metaanálisis de ángulos 
  articulares en el saque de tenis (2024)
- **Elliott, B. et al.** — Análisis cinemático del saque, rotación 
  externa máxima del hombro
- **Bradley, P. et al.** — Factores de riesgo de dolor lumbar y 
  pinzamiento femoroacetabular en tenistas

---

## Aviso importante

> Este proyecto es un prototipo educativo desarrollado con fines de 
> aprendizaje e investigación personal. Los resultados que genera 
> **no reemplazan** la evaluación de un entrenador certificado, un 
> fisioterapeuta ni ningún profesional de la salud o del deporte. 
> Ante cualquier dolor, molestia o duda sobre tu técnica, consulta 
> siempre con un profesional.
