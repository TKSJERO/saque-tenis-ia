# verificar_instalacion.py
# Script de prueba de humo para el Analizador de Saque de Tenis.
# Verifica que Python, las librerías y los modelos estén listos para usar.
# Uso: python verificar_instalacion.py (con el entorno virtual activo)

import sys

# Forzamos la salida de texto en UTF-8 para que los caracteres especiales
# funcionen correctamente en la terminal de Windows.
sys.stdout.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# COLORES PARA LA TERMINAL
# Estas son secuencias de escape ANSI: códigos especiales que la terminal
# interpreta como colores. No son visibles en el texto, solo cambian el color.
# ─────────────────────────────────────────────────────────────────────────────
VERDE    = "\033[92m"
ROJO     = "\033[91m"
AMARILLO = "\033[93m"
AZUL     = "\033[94m"
NEGRITA  = "\033[1m"
RESET    = "\033[0m"  # Vuelve al color normal de la terminal

def ok(texto):
    """Imprime un mensaje de éxito en verde con un check."""
    print(f"  {VERDE}[OK] {texto}{RESET}")

def error(texto):
    """Imprime un mensaje de error en rojo con una X."""
    print(f"  {ROJO}[ERROR] {texto}{RESET}")

def advertencia(texto):
    """Imprime una advertencia en amarillo."""
    print(f"  {AMARILLO}[AVISO] {texto}{RESET}")

def titulo(texto):
    """Imprime un título en azul y negrita."""
    print(f"\n{AZUL}{NEGRITA}{texto}{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# ENCABEZADO
# ─────────────────────────────────────────────────────────────────────────────
print()
print(NEGRITA + "=" * 55 + RESET)
print(NEGRITA + "   Verificacion del entorno" + RESET)
print(NEGRITA + "   Analizador de Saque de Tenis" + RESET)
print(NEGRITA + "=" * 55 + RESET)


# ─────────────────────────────────────────────────────────────────────────────
# PASO 1: VERIFICAR LA VERSIÓN DE PYTHON
# sys.version_info devuelve la versión de Python como números separados.
# Por ejemplo, Python 3.12.10 → major=3, minor=12, micro=10
# ─────────────────────────────────────────────────────────────────────────────
titulo("1. Versión de Python")

version_actual = sys.version_info
version_texto  = f"{version_actual.major}.{version_actual.minor}.{version_actual.micro}"

if version_actual.major == 3 and version_actual.minor == 12:
    ok(f"Python {version_texto} — versión correcta para este proyecto")
else:
    advertencia(
        f"Python {version_texto} detectado. "
        f"Este proyecto requiere Python 3.12.x — "
        f"MediaPipe no soporta versiones más nuevas."
    )


# ─────────────────────────────────────────────────────────────────────────────
# PASO 2: IMPORTAR Y VERIFICAR CADA LIBRERÍA
# Un bloque try/except intenta ejecutar el código dentro de "try".
# Si algo falla, en lugar de detener el script con un error feo,
# captura el problema y lo muestra de forma clara en "except".
# ─────────────────────────────────────────────────────────────────────────────
titulo("2. Librerías instaladas")

# Lista para registrar qué falló (la usaremos en el resumen final)
errores = []

# — MediaPipe —
try:
    import mediapipe as mp
    ok(f"mediapipe      versión {mp.__version__}")
except ImportError as e:
    error(f"mediapipe      NO encontrado → {e}")
    errores.append("mediapipe")

# — OpenCV (cv2 es el nombre del paquete dentro de Python) —
try:
    import cv2
    ok(f"opencv-python  versión {cv2.__version__}")
except ImportError as e:
    error(f"opencv-python  NO encontrado → {e}")
    errores.append("opencv-python")

# — NumPy —
try:
    import numpy as np
    ok(f"numpy          versión {np.__version__}")
except ImportError as e:
    error(f"numpy          NO encontrado → {e}")
    errores.append("numpy")

# — Streamlit —
try:
    import streamlit as st
    ok(f"streamlit      versión {st.__version__}")
except ImportError as e:
    error(f"streamlit      NO encontrado → {e}")
    errores.append("streamlit")


# ─────────────────────────────────────────────────────────────────────────────
# PASO 3: PRUEBAS FUNCIONALES
# Importar una librería confirma que está instalada, pero no que funciona.
# Estas pruebas verifican que cada herramienta puede hacer trabajo real.
# ─────────────────────────────────────────────────────────────────────────────
titulo("3. Pruebas funcionales")

# — Prueba de MediaPipe: verificar que la API de Tasks está disponible —
# MediaPipe 0.10+ usa la nueva API "Tasks" en lugar de la antigua "Solutions".
# Importamos el módulo de visión para confirmar que MediaPipe está operativo.
# El modelo de pose (.task) se descargará en la próxima sesión de desarrollo.
try:
    from mediapipe.tasks.python import vision as mp_vision
    # Verificamos que PoseLandmarker (el detector de pose) existe en el módulo
    assert hasattr(mp_vision, "PoseLandmarker"), "PoseLandmarker no encontrado"
    ok("MediaPipe Tasks API — modulo de vision disponible y listo")
except Exception as e:
    error(f"MediaPipe Tasks API — fallo al verificar el modulo → {e}")
    errores.append("mediapipe (tasks api)")

# — Prueba de NumPy: crear un array y hacer una operación —
# Un "array" es una lista de números optimizada para cálculos matemáticos.
# Aquí creamos [1.0, 2.0, 3.0] y calculamos su promedio (debe dar 2.0).
try:
    import numpy as np
    datos_prueba = np.array([1.0, 2.0, 3.0])
    promedio     = np.mean(datos_prueba)
    assert promedio == 2.0, "El cálculo de promedio dio un resultado inesperado"
    ok(f"NumPy          — operación de prueba correcta (promedio = {promedio})")
except Exception as e:
    error(f"NumPy          — falló la operación de prueba → {e}")
    errores.append("numpy (operación)")

# — Prueba de OpenCV: leer información del sistema —
# getBuildInformation() devuelve un texto con cómo fue compilado OpenCV.
# Si esto responde, OpenCV está funcionando. No abre cámara ni archivos.
try:
    import cv2
    info = cv2.getBuildInformation()
    # Verificamos que la respuesta tenga contenido real (más de 10 caracteres)
    assert len(info) > 10, "La información de OpenCV está vacía"
    ok("OpenCV         — responde correctamente al sistema")
except Exception as e:
    error(f"OpenCV         — falló la prueba del sistema → {e}")
    errores.append("opencv (sistema)")


# ─────────────────────────────────────────────────────────────────────────────
# PASO 4: RESUMEN FINAL
# ─────────────────────────────────────────────────────────────────────────────
print()
print(NEGRITA + "=" * 55 + RESET)

if not errores:
    # Todo salió bien
    print(VERDE + NEGRITA + "  TODO LISTO PARA EMPEZAR  [OK]" + RESET)
    print(NEGRITA + "=" * 55 + RESET)
    print()
    print("  Próximos pasos:")
    print("  1. Conseguir un video mp4 de saque de tenis (vista lateral)")
    print("  2. Colocarlo en la carpeta  videos/prueba/propios/")
    print("  3. Arrancar la sesión de desarrollo del Hito 1:")
    print("     → Leer el video con OpenCV frame a frame")
    print("     → Extraer los keypoints con MediaPipe Pose")
    print("     → Guardar los keypoints en datos/keypoints/")
    print()
else:
    # Algo falló
    print(ROJO + NEGRITA + "  ATENCION: hay errores que resolver  [ERROR]" + RESET)
    print(NEGRITA + "=" * 55 + RESET)
    print()
    print(f"  {ROJO}Falló:{RESET}")
    for item in errores:
        print(f"    • {item}")
    print()
    print("  Qué hacer:")
    print("  1. Asegúrate de que el entorno virtual esté activo")
    print("     Debes ver (venv) al inicio del prompt de PowerShell")
    print("  2. Reinstala las librerías con:")
    print("     pip install -r requirements.txt")
    print("  3. Si el error persiste, copia el mensaje y consúltalo")
    print()

print(NEGRITA + "=" * 55 + RESET)
print()
