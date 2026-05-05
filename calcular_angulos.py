"""
calcular_angulos.py — Script principal del Hito 3.

Uso:
    python calcular_angulos.py <ruta_json_keypoints> [ruta_json_fases]

Ejemplos:
    python calcular_angulos.py datos/keypoints/video_pro_keypoints.json
    python calcular_angulos.py datos/keypoints/video_pro_keypoints.json datos/resultados/video_pro_fases.json

El script:
  1. Lee el JSON de keypoints generado por el Hito 1
  2. Auto-descubre el JSON de fases en datos/resultados/ (o lo recibe como argumento)
  3. Calcula ~10 ángulos articulares por frame
  4. Extrae el valor representativo por fase y lo evalúa contra rangos biomecánicos
  5. Guarda el resultado en datos/angulos/{video}_angulos.json
  6. Imprime tabla de validación con: parámetro | valor | rango ideal | evaluación | confiable_2d
"""

import sys
import json
from pathlib import Path

# Raíz del proyecto
RAIZ = Path(__file__).parent
sys.path.insert(0, str(RAIZ))

from src.angulos.calculador_angulos import calcular_todos_los_angulos


# ─────────────────────────────────────────────────────────────
# TABLA DE VALIDACIÓN
# ─────────────────────────────────────────────────────────────

# Etiquetas legibles para cada parámetro
ETIQUETAS_PARAMETROS = {
    "flexion_rodilla_delantera":    "Flexión rodilla delantera",
    "flexion_rodilla_trasera":      "Flexión rodilla trasera",
    "inclinacion_tronco_vertical":  "Tronco vs vertical (Trophy)",
    "separacion_lateral":           "Separación lateral hombro-pelvis",
    "mer_hombro_proxy":             "MER hombro (proxy 2D)",
    "inclinacion_pelvica":          "Inclinación pélvica (proxy 2D)",
    "abduccion_hombro":             "Abducción hombro (Contact)",
    "flexion_codo":                 "Flexión codo (Contact)",
    "inclinacion_tronco_horizontal":"Tronco vs horizontal (Contact)",
    "desviacion_muneca":            "Desviación muñeca (proxy 2D)",
    "rom_rotacion_interna":         "RoM rotación interna (proxy 2D)",
}

SIMBOLOS_EVALUACION = {
    "optimo":       "OPTIMO",
    "aceptable":    "ACEPTABLE",
    "deficiente":   "DEFICIENTE",
    "excesivo":     "EXCESIVO",
    "no_evaluable": "—",
}


def imprimir_tabla_validacion(resumen):
    """
    Imprime la tabla de resultados del Hito 3.
    Columnas: parámetro | valor | rango ideal | evaluación | confiable_2d
    """
    print("\n" + "=" * 82)
    print("RESULTADOS DE ÁNGULOS ARTICULARES — HITO 3")
    print("=" * 82)
    print(f"  {'Parámetro':<35} {'Valor':>7}  {'Rango ideal':>14}  {'Evaluación':>10}  {'2D?':>4}")
    print("-" * 82)

    for clave, datos in resumen.items():
        etiqueta    = ETIQUETAS_PARAMETROS.get(clave, clave)
        valor       = datos.get("valor")
        r_min       = datos.get("rango_ideal_min")
        r_max       = datos.get("rango_ideal_max")
        evaluacion  = datos.get("evaluacion", "—")
        confiable   = datos.get("confiable_2d", False)
        r_acep      = datos.get("rango_minimo_aceptable")

        # Formatear valor
        valor_str = f"{valor:.1f}°" if valor is not None else "—"

        # Formatear rango ideal
        if r_min is not None and r_max is not None:
            rango_str = f"{r_min:.0f}°–{r_max:.0f}°"
        else:
            rango_str = "sin rango"

        # Agregar rango mínimo aceptable si existe
        if r_acep is not None:
            rango_str += f" (>{r_acep:.0f}°)"

        # Símbolo de evaluación
        eval_str = SIMBOLOS_EVALUACION.get(evaluacion, evaluacion)

        # Confiabilidad 2D
        conf_str = "Sí" if confiable else "No*"

        print(f"  {etiqueta:<35} {valor_str:>7}  {rango_str:>14}  {eval_str:>10}  {conf_str:>4}")

    print("-" * 82)
    print("  * Parámetros marcados 'No' tienen baja confiabilidad desde vista lateral.")
    print("    Sus valores son orientativos; ver campo 'advertencia' en el JSON.")
    print("=" * 82 + "\n")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    # ── 1. Leer argumentos ────────────────────────────────────────────────
    if len(sys.argv) < 2:
        print("Uso: python calcular_angulos.py <ruta_json_keypoints> [ruta_json_fases]")
        print("Ejemplo: python calcular_angulos.py datos/keypoints/video_pro_keypoints.json")
        sys.exit(1)

    ruta_keypoints = Path(sys.argv[1])
    if not ruta_keypoints.exists():
        print(f"Error: no se encontró el archivo JSON de keypoints: {ruta_keypoints}")
        sys.exit(1)

    # ── 2. Descubrir JSON de fases ─────────────────────────────────────────
    ruta_fases = None

    if len(sys.argv) >= 3:
        ruta_fases = Path(sys.argv[2])
        if not ruta_fases.exists():
            print(f"Error: no se encontró el archivo JSON de fases: {ruta_fases}")
            sys.exit(1)
    else:
        # Auto-descubrir: buscar en datos/resultados/ un JSON cuyo nombre
        # contenga el mismo nombre base que el JSON de keypoints
        # Ej: "video_pro_keypoints.json" → busca "video_pro_fases.json"
        nombre_base = ruta_keypoints.stem.replace("_keypoints", "")
        carpeta_resultados = RAIZ / "datos" / "resultados"

        if carpeta_resultados.exists():
            candidatos = list(carpeta_resultados.glob(f"{nombre_base}_fases.json"))
            if candidatos:
                ruta_fases = candidatos[0]

        if ruta_fases is None:
            print(f"Error: no se encontró el JSON de fases para '{nombre_base}'.")
            print(f"  Buscado en: {carpeta_resultados}")
            print(f"  Pasá la ruta manualmente como segundo argumento:")
            print(f"    python calcular_angulos.py {ruta_keypoints} <ruta_fases.json>")
            sys.exit(1)

    print(f"Keypoints : {ruta_keypoints}")
    print(f"Fases     : {ruta_fases}")

    # ── 3. Cargar JSONs ────────────────────────────────────────────────────
    with open(ruta_keypoints, "r", encoding="utf-8") as f:
        datos_keypoints = json.load(f)

    with open(ruta_fases, "r", encoding="utf-8") as f:
        datos_fases = json.load(f)

    # ── 4. Calcular ángulos ────────────────────────────────────────────────
    resultado = calcular_todos_los_angulos(datos_keypoints, datos_fases)

    # ── 5. Guardar JSON de salida ──────────────────────────────────────────
    carpeta_angulos = RAIZ / "datos" / "angulos"
    carpeta_angulos.mkdir(parents=True, exist_ok=True)

    nombre_base = ruta_keypoints.stem.replace("_keypoints", "")
    ruta_salida = carpeta_angulos / f"{nombre_base}_angulos.json"

    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"JSON guardado en: {ruta_salida}")

    # ── 6. Imprimir tabla de validación ────────────────────────────────────
    imprimir_tabla_validacion(resultado["resumen_por_fase"])


if __name__ == "__main__":
    main()
