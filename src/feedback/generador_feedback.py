"""
generador_feedback.py — Módulo del Hito 4.

Genera feedback biomecánico en lenguaje natural usando la API de Claude.
Recibe el JSON de ángulos del Hito 3 y devuelve un análisis tipo entrenador.

Funciones:
    cargar_datos_angulos(ruta_json)         → dict con datos del saque
    construir_input_para_claude(datos)      → texto estructurado para la API
    generar_feedback(input_estructurado)    → (texto_feedback, metricas)
    guardar_feedback(texto, ruta_salida)    → guarda .md y muestra en consola
"""

import os
import json
import time
from pathlib import Path

from dotenv import load_dotenv
import anthropic

# Cargar variables de entorno desde .env
load_dotenv()


# ============================================================
# SYSTEM PROMPT — Personalidad y reglas del entrenador
# Para iterar el comportamiento del feedback, editar aquí.
# Versión aprobada: 2026-04-14
# ============================================================
SYSTEM_PROMPT = """Eres un entrenador de tenis especializado en biomecánica del saque.
Analizas datos de movimiento y entregas feedback técnico claro,
específico y accionable. Hablas en español neutro, con tono
profesional y directo — como un entrenador que respeta al atleta
y va al punto. No usas lenguaje motivacional genérico. Cada
comentario tiene una razón biomecánica concreta.


== REGLAS DE EVALUACIÓN ==

Recibirás datos estructurados del saque organizados por fase.
Cada parámetro tiene: valor medido, rango de referencia,
evaluación y flag de confiabilidad 2D. Aplica estas reglas:

1. ÓPTIMO: No le dediques sección. Si hay varios valores óptimos,
   mencionarlos en el resumen en una sola oración positiva.

2. ACEPTABLE: Una oración indicando que está en el límite mínimo
   pero no es prioridad urgente. Sin bullet propio.

3. DEFICIENTE o EXCESIVO: Genera un bullet de MÁXIMO 40
   palabras que combine en una o dos oraciones cortas:
   - El problema (qué está fuera de rango y cuánto)
   - La corrección (verbo imperativo directo + acción concreta)
   - El por qué (razón biomecánica en 5-8 palabras)

   Estilo obligatorio — directo, sin adjetivos innecesarios,
   sin frases introductorias. Ejemplo (22 palabras):
   "Rodilla trasera con 42° (necesitas 51°+). Baja más el
   centro de masa antes del impulso. Sin esa carga, el saque
   pierde potencia desde el suelo."

   Verbos imperativos directos: "flexiona", "lleva", "rota",
   "baja", "inclina". NUNCA: "mejora", "trabaja en", "intenta".

4. CONFIABLE_2D = FALSE: Marca el parámetro con asterisco (*).
   Usa lenguaje condicional ("sugiere", "podría indicar"). Si está
   fuera de rango, incluye el bullet igualmente pero con asterisco
   visible antes del nombre del parámetro.

5. TRONCO EN CONTACT (inclinacion_tronco_horizontal): Este
   parámetro tiene una discrepancia conocida entre el sistema de
   medición y la referencia bibliográfica. No lo evalúes como
   deficiente ni excesivo. Inclúyelo solo en la sección de
   Limitaciones con este texto exacto, reemplazando el valor:
   "La inclinación del tronco en el impacto registró [VALOR]° —
   valor en revisión por diferencia entre método de medición 2D
   y fuente bibliográfica."

6. TODO EN RANGO: Si todos los parámetros confiables están en
   óptimo o aceptable, escribe un feedback breve (máximo 4
   oraciones) reconociendo los puntos fuertes. No inventes
   problemas ni rellenes.

7. NO INVENTAR DATOS: Solo evalúa parámetros que recibas en el
   input. Si un parámetro no aparece en los datos, no lo
   menciones, no asumas valores. Si recibes un valor "None" o
   "no_evaluable", omítelo del feedback completamente — no digas
   "no se pudo medir", simplemente no lo menciones.

8. ECONOMÍA DE PALABRAS: No uses muletillas como "presenta",
   "muestra", "se observa que", "podría comprometer", "que
   podría". Si una frase se puede decir con menos palabras sin
   perder precisión técnica, hazlo. Cada palabra debe ganarse
   su lugar.


== ESTRUCTURA DE SALIDA OBLIGATORIA ==

Usa exactamente este formato Markdown. Omite una sección de fase
completa si no hay parámetros fuera de rango en ella.

---

## Análisis biomecánico del saque

**Resumen general**
[Máximo 3 oraciones. Panorama global: qué fue sólido, qué
necesita atención, tono general.]

**Loading — Fase de carga**
[Contexto de la fase en MÁXIMO 15 palabras.]
- **[Nombre del parámetro]**: [Problema.] [Corrección.] [Por qué importa.]

**Cocking — Trophy Position**
[Contexto de la fase en MÁXIMO 15 palabras.]
- **[Nombre del parámetro]**: [Problema.] [Corrección.] [Por qué importa.]

**Contact — Impacto**
[Contexto de la fase en MÁXIMO 15 palabras.]
- **[Nombre del parámetro]**: [Problema.] [Corrección.] [Por qué importa.]

**Limitaciones del análisis**
*Los parámetros marcados con * se estimaron en vista lateral 2D.
Esta perspectiva limita la precisión en rotaciones y planos
frontales — tómalos como orientativos, no como diagnóstico
definitivo.*
[Si aplica: nota del tronco en Contact con el valor en grados.]

---

LONGITUD OBLIGATORIA: 250-400 palabras totales. Si superas
400 palabras, has fallado la tarea — recorta hasta cumplir
sin perder información técnica."""


# ============================================================
# MAPEO DE NOMBRES: clave del JSON → nombre legible en español
# ============================================================
NOMBRES_LEGIBLES = {
    'flexion_rodilla_delantera':    'Flexión de rodilla delantera',
    'flexion_rodilla_trasera':      'Flexión de rodilla trasera',
    'inclinacion_tronco_vertical':  'Inclinación del tronco (vs vertical)',
    'separacion_lateral':           'Separación lateral hombro-pelvis',
    'mer_hombro_proxy':             'Rotación externa del hombro',
    'inclinacion_pelvica':          'Inclinación pélvica',
    'abduccion_hombro':             'Abducción de hombro',
    'flexion_codo':                 'Flexión de codo',
    'inclinacion_tronco_horizontal':'Inclinación del tronco (vs horizontal)',
    'desviacion_muneca':            'Desviación de muñeca',
    'rom_rotacion_interna':         'RoM rotación interna',
}

# Fases con respaldo bibliográfico, en orden de aparición en el saque
FASES_INCLUIDAS = ['loading', 'cocking', 'contact']

FASES_NOMBRES = {
    'loading': 'Loading — Fase de carga',
    'cocking': 'Cocking — Trophy Position',
    'contact': 'Contact — Impacto',
}

# Modelo y parámetros de generación
MODELO      = 'claude-sonnet-4-6'
MAX_TOKENS  = 2048
TEMPERATURE = 0.3

# Precios por millón de tokens (claude-sonnet-4-6, abril 2026)
PRECIO_INPUT_POR_MILLON  = 3.0
PRECIO_OUTPUT_POR_MILLON = 15.0


# ------------------------------------------------------------

def cargar_datos_angulos(ruta_json):
    """Lee el JSON de ángulos generado por calcular_angulos.py (Hito 3)."""
    ruta = Path(ruta_json)
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_json}")
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)


def construir_input_para_claude(datos_angulos):
    """Formatea los datos de ángulos como texto estructurado legible.

    No se pasa JSON crudo — el texto con secciones y etiquetas claras
    mejora la comprensión de Claude y facilita el debugging si algo
    sale mal en el formato.

    Solo incluye las fases con respaldo bibliográfico (loading, cocking,
    contact). Omite parámetros con evaluacion='no_evaluable' (regla 7).
    El parámetro inclinacion_tronco_horizontal recibe una nota especial
    para que Claude lo trate solo en la sección de Limitaciones.
    """
    resumen = datos_angulos.get('resumen_por_fase', {})

    # Agrupar parámetros por fase, filtrando fases y evaluaciones excluidas
    por_fase = {fase: [] for fase in FASES_INCLUIDAS}

    for nombre_param, datos in resumen.items():
        fase       = datos.get('fase', '')
        evaluacion = datos.get('evaluacion', '')

        if fase not in FASES_INCLUIDAS:
            continue  # deceleration, finish, etc. — sin rangos bibliográficos
        if evaluacion == 'no_evaluable':
            continue  # regla 7: no mencionar lo que no se pudo medir

        por_fase[fase].append((nombre_param, datos))

    # Construir el texto línea a línea
    lineas = ['DATOS DEL SAQUE ANALIZADO', '']

    for fase in FASES_INCLUIDAS:
        params = por_fase[fase]
        if not params:
            continue

        lineas.append(f'{FASES_NOMBRES[fase]}:')

        for nombre_param, datos in params:
            nombre_legible     = NOMBRES_LEGIBLES.get(nombre_param, nombre_param)
            valor              = datos.get('valor')
            evaluacion         = datos.get('evaluacion', '')
            confiable          = datos.get('confiable_2d', False)
            rango_min          = datos.get('rango_ideal_min')
            rango_max          = datos.get('rango_ideal_max')
            rango_min_aceptable= datos.get('rango_minimo_aceptable')

            # Saltar si el valor es None (regla 7)
            if valor is None:
                continue

            lineas.append(f'- {nombre_legible}: {valor:.1f}°')

            # Rango ideal (con mínimo aceptable alternativo si existe)
            if rango_min is not None and rango_max is not None:
                rango_str = f'{rango_min}°–{rango_max}°'
                if rango_min_aceptable is not None:
                    rango_str += f' (mínimo aceptable: {rango_min_aceptable}°)'
                lineas.append(f'  Rango ideal: {rango_str}')

            lineas.append(f'  Evaluación: {evaluacion.upper()}')
            lineas.append(f'  Confiable en 2D: {"Sí" if confiable else "No"}')

            # Nota especial para el parámetro con discrepancia bibliográfica
            if nombre_param == 'inclinacion_tronco_horizontal':
                lineas.append(
                    f'  NOTA ESPECIAL: No evaluar como deficiente/excesivo. '
                    f'Incluir únicamente en sección Limitaciones con el valor {valor:.1f}°.'
                )

            lineas.append('')  # línea en blanco entre parámetros

    return '\n'.join(lineas)


def generar_feedback(input_estructurado):
    """Llama a la API de Claude y devuelve el texto del feedback más métricas.

    Retorna una tupla: (texto_feedback: str, metricas: dict)
    metricas contiene tokens_input, tokens_output, tiempo_segundos, costo_usd.
    """
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key or api_key.strip() == '':
        raise ValueError("No se encontró ANTHROPIC_API_KEY en .env")

    cliente = anthropic.Anthropic(api_key=api_key)

    try:
        inicio = time.time()

        respuesta = cliente.messages.create(
            model=MODELO,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=SYSTEM_PROMPT,
            messages=[
                {'role': 'user', 'content': input_estructurado}
            ]
        )

        tiempo_segundos = round(time.time() - inicio, 2)

        texto_feedback = respuesta.content[0].text

        metricas = {
            'tokens_input':    respuesta.usage.input_tokens,
            'tokens_output':   respuesta.usage.output_tokens,
            'tiempo_segundos': tiempo_segundos,
            'costo_usd': round(
                (respuesta.usage.input_tokens  / 1_000_000 * PRECIO_INPUT_POR_MILLON) +
                (respuesta.usage.output_tokens / 1_000_000 * PRECIO_OUTPUT_POR_MILLON),
                5
            )
        }

        return texto_feedback, metricas

    except anthropic.AuthenticationError:
        raise RuntimeError("API key inválida o revocada. Verifica el archivo .env")
    except anthropic.PermissionDeniedError:
        raise RuntimeError("Sin créditos o sin permisos. Verifica tu cuenta en console.anthropic.com")
    except anthropic.APIConnectionError:
        raise RuntimeError("Sin conexión a internet o el servidor no responde")
    except anthropic.RateLimitError:
        raise RuntimeError("Límite de solicitudes alcanzado. Espera unos segundos e intenta de nuevo")
    except anthropic.APIStatusError as e:
        raise RuntimeError(f"Error de la API (código {e.status_code}): {e.message}")


def guardar_feedback(texto_feedback, ruta_salida):
    """Guarda el feedback como archivo Markdown y lo imprime en consola."""
    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(texto_feedback)

    # Mostrar en consola también (sin abrir el archivo)
    print('\n' + '=' * 60)
    print('FEEDBACK GENERADO:')
    print('=' * 60)
    print(texto_feedback)
    print('=' * 60)
    print(f'Guardado en: {ruta_salida}')
