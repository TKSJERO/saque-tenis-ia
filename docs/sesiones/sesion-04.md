# Sesión 04 — Hito 4: Generación de feedback en lenguaje natural

**Fecha:** 2026-04-15
**Estado al inicio:** Hitos 1–3 completados. Feedback pendiente.
**Estado al cierre:** Hito 4 completado. 4/5 hitos del pipeline listos.

---

## Objetivo de la sesión

Construir el módulo que toma el JSON de ángulos del Hito 3 y genera
feedback biomecánico en lenguaje natural usando la API de Claude.

---

## Lo que se construyó

### Archivos creados

- `src/feedback/generador_feedback.py` — módulo principal con 4 funciones:
  `cargar_datos_angulos`, `construir_input_para_claude`, `generar_feedback`,
  `guardar_feedback`. Incluye system prompt, mapeo de nombres, y manejo de errores.
- `generar_feedback.py` — script de entrada en raíz. Acepta ruta al JSON de
  ángulos como argumento. Imprime métricas (tokens, tiempo, costo) y guarda
  el resultado en `datos/feedback/`.
- `src/feedback/test_conexion.py` — test mínimo de conectividad con la API.
- `.env` — archivo con `ANTHROPIC_API_KEY` (excluido del repositorio).

### Flujo de datos

```
datos/angulos/video_pro_angulos.json
        ↓  cargar_datos_angulos()
    dict con resumen_por_fase
        ↓  construir_input_para_claude()
    texto estructurado (filtra no_evaluable, agrega notas especiales)
        ↓  generar_feedback() → API de Claude
    texto Markdown + métricas
        ↓  guardar_feedback()
datos/feedback/video_pro_feedback.md
```

---

## Decisiones técnicas tomadas

### Modelo y parámetros
- Modelo: `claude-sonnet-4-6`
- Temperature: 0.3 — variabilidad controlada sin alucinaciones
- max_tokens: 2048 (se empezó con 1024, generó respuesta truncada, se subió)

### System prompt — reglas implementadas
1. ÓPTIMO: solo en resumen, una oración positiva
2. ACEPTABLE: una oración, sin bullet propio
3. DEFICIENTE/EXCESIVO: bullet de máximo 40 palabras (problema + corrección imperativa + razón biomecánica)
4. confiable_2d=False: marca con asterisco (\*), lenguaje condicional
5. Tronco en Contact: solo en Limitaciones, texto fijo, no evaluado como error
6. TODO EN RANGO: feedback breve de 4 oraciones máximo
7. No inventar datos: omitir silenciosamente lo que no llega en el input
8. Economía de palabras: sin muletillas, cada palabra se gana su lugar

### Tronco en Contact
El sistema mide ~79° mientras el paper indica 41°–55°. Causa: probable diferencia
de convención (cadera→hombros vs cadera→C7) o diferencia 2D/3D. Decisión: excluir
de evaluación, incluir en Limitaciones como "valor en revisión".

### Gestión de API key
`.env` + `python-dotenv`. La clave nunca aparece en el código. `.env` está en
`.gitignore`.

---

## Iteración del system prompt

### Primera versión → 666 palabras (excede límite 250–400)
- Problema: bullets con 3 oraciones completas, frases introductorias en contexto de fase

### Cambios aplicados en iteración 1:
1. Regla 3: "exactamente 3 oraciones" → "MÁXIMO 40 palabras en una o dos cortas"
2. Regla 8 nueva: economía de palabras, sin muletillas
3. Contexto de fase: "1 oración" → "MÁXIMO 15 palabras"
4. Longitud: "objetivo" → "OBLIGATORIA — si superas 400 palabras, has fallado la tarea"

### Segunda versión → 374 palabras ✓
Todos los criterios superados. Hito cerrado en 1 iteración.

---

## Resultado final del feedback (video_pro.mp4)

**Parámetros evaluados:** 8 (de 11 total — 3 filtrados como no_evaluable)
**Parámetros fuera de rango:** 5 con bullet de corrección
**Parámetros óptimos/aceptables:** 3 mencionados en resumen o contexto
**Palabras totales:** 374
**Costo:** ~$0.018–$0.024 USD por análisis

### Hallazgos principales del análisis biomecánico
- Trophy position concentra 3 déficits simultáneos (rodilla trasera, inclinación tronco, rotación externa hombro)
- Codo llega casi extendido al impacto (10° vs rango 16°–46°)
- Desviación de muñeca es el único parámetro óptimo confirmado
- Abducción de hombro y separación lateral marcados con asterisco (no confiables desde lateral 2D)

---

## Métricas de la llamada final
- Tokens input: 1,999
- Tokens output: 769
- Tiempo de respuesta: 13.84 segundos
- Costo: $0.018 USD

---

## Estado del pipeline al cierre de sesión

| Hito | Módulo | Estado |
|---|---|---|
| 1 | Detección de pose (MediaPipe) | COMPLETADO |
| 2 | Identificación de fases | COMPLETADO |
| 3 | Cálculo de ángulos + evaluación | COMPLETADO |
| 4 | Generación de feedback (API Claude) | COMPLETADO |
| 5 | Interfaz Streamlit | PENDIENTE |

---

## Próxima sesión — Hito 5: Interfaz Streamlit

Objetivo: app web simple con Streamlit que orqueste TODO el pipeline desde un video.

El usuario sube un `.mp4` → la app ejecuta los 4 módulos en secuencia →
muestra el feedback biomecánico en pantalla.

Preguntas abiertas a resolver al inicio del Hito 5:
- ¿Se reprocesan los keypoints y fases cada vez, o se cachea si ya existe el JSON?
- ¿Cómo se muestra el progreso mientras el pipeline corre (barra de progreso, mensajes)?
- ¿Se muestra el video con esqueleto en la interfaz, o solo el feedback de texto?
- ¿Se incluye el video con etiquetas de fases, o solo el feedback final?
