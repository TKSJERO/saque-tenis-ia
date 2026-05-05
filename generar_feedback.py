"""
generar_feedback.py — Script principal del Hito 4.

Uso:
    python generar_feedback.py <ruta_json_angulos>

Ejemplo:
    python generar_feedback.py datos/angulos/video_pro_angulos.json

El script:
  1. Lee el JSON de ángulos generado por el Hito 3
  2. Formatea los datos como texto estructurado
  3. Muestra el input que se enviará a Claude (para verificar antes de gastar tokens)
  4. Llama a la API de Claude (claude-sonnet-4-6)
  5. Imprime el feedback en consola y lo guarda en datos/feedback/{video}_feedback.md
  6. Muestra tiempo de respuesta, tokens consumidos y costo estimado
"""

import sys
from pathlib import Path

# Asegurar que la raíz del proyecto esté en el path para los imports
RAIZ = Path(__file__).parent
sys.path.insert(0, str(RAIZ))

from src.feedback.generador_feedback import (
    cargar_datos_angulos,
    construir_input_para_claude,
    generar_feedback,
    guardar_feedback,
)


def main():
    # Verificar argumento
    if len(sys.argv) < 2:
        print("Uso: venv\\Scripts\\python generar_feedback.py <ruta_json_angulos>")
        print("Ejemplo: venv\\Scripts\\python generar_feedback.py datos/angulos/video_pro_angulos.json")
        sys.exit(1)

    ruta_json = sys.argv[1]

    # 1. Cargar datos del Hito 3
    print(f"\nCargando datos de ángulos: {ruta_json}")
    datos = cargar_datos_angulos(ruta_json)
    print(f"Parámetros cargados: {len(datos.get('resumen_por_fase', {}))}")

    # 2. Construir input formateado para Claude
    input_estructurado = construir_input_para_claude(datos)

    # 3. Mostrar el input antes de llamar a la API
    #    (para verificar que el formato es correcto y no gastar tokens en vano)
    print('\n' + '=' * 60)
    print('INPUT QUE SE ENVIARÁ A CLAUDE:')
    print('=' * 60)
    print(input_estructurado)
    print('=' * 60)

    # 4. Llamar a la API
    print(f"\nLlamando a la API de Claude (claude-sonnet-4-6)...")
    texto_feedback, metricas = generar_feedback(input_estructurado)

    # 5. Mostrar métricas de uso
    print(f"\nTiempo de respuesta : {metricas['tiempo_segundos']}s")
    print(f"Tokens input        : {metricas['tokens_input']}")
    print(f"Tokens output       : {metricas['tokens_output']}")
    print(f"Costo estimado      : ${metricas['costo_usd']}")

    # 6. Guardar en datos/feedback/ e imprimir en consola
    nombre_video = Path(ruta_json).stem.replace('_angulos', '')
    ruta_salida  = f"datos/feedback/{nombre_video}_feedback.md"
    guardar_feedback(texto_feedback, ruta_salida)


if __name__ == '__main__':
    main()
