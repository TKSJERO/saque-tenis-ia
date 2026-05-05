# estilos.py
# Inyecta Google Fonts y CSS custom en la app Streamlit.
# Se llama una sola vez al inicio de app.py con inyectar_css().

import streamlit as st


def inyectar_css():
    """Carga Space Grotesk + JetBrains Mono y aplica estilos visuales."""
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">

        <style>
        /* ── Tipografía base ── */
        html, body, [class*="css"] {
            font-family: 'Space Grotesk', sans-serif;
        }

        h1, h2, h3, h4 {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 600;
        }

        /* ── Números y valores biomecánicos ── */
        .dato-numerico {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.95rem;
        }

        /* ── Ancho máximo del contenido central ── */
        /* padding-top debe superar la barra fija de Streamlit (~58px = ~3.6rem) */
        .block-container {
            max-width: 860px;
            padding-top: 5rem;
            padding-bottom: 3rem;
        }

        /* ── Header de la app ── */
        .app-titulo {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: #A8E063;
            letter-spacing: -0.02em;
            line-height: 1.25;
            margin-top: 0;
            margin-bottom: 0.1rem;
        }

        .app-subtitulo {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.95rem;
            color: #888;
            margin-bottom: 2rem;
            font-weight: 400;
        }

        /* ── Separador delgado ── */
        .separador {
            border: none;
            border-top: 1px solid #2A2D38;
            margin: 1.5rem 0;
        }

        /* ── Estado de progreso completado ── */
        .paso-completo {
            color: #2DD4BF;
            font-weight: 500;
        }

        /* ── Estado de progreso con cache ── */
        .paso-cacheado {
            color: #888;
            font-style: italic;
        }

        /* ── Tarjeta de costo/métricas ── */
        .metrica-footer {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            color: #666;
            text-align: right;
            padding-top: 0.75rem;
            border-top: 1px solid #2A2D38;
            margin-top: 1.5rem;
        }

        /* ── Advertencia de video vertical ── */
        .advertencia-vertical {
            background-color: #1C1E26;
            border-left: 3px solid #F5A623;
            padding: 0.75rem 1rem;
            border-radius: 4px;
            font-size: 0.9rem;
            color: #E8E8E8;
            margin-bottom: 1rem;
        }

        /* ── Estilo del bloque de feedback ── */
        .feedback-container {
            background-color: #1C1E26;
            border-radius: 8px;
            padding: 1.5rem 1.75rem;
            line-height: 1.7;
        }

        .feedback-container strong {
            color: #A8E063;
        }

        /* ── Botón de upload más visible ── */
        [data-testid="stFileUploader"] {
            background-color: #1C1E26;
            border-radius: 8px;
            padding: 0.5rem;
        }

        /* ── Expanders con borde sutil ── */
        [data-testid="stExpander"] {
            border: 1px solid #2A2D38;
            border-radius: 8px;
        }

        /* ── Negritas del feedback en verde lima ── */
        [data-testid="stMarkdownContainer"] strong {
            color: #A8E063;
        }

        /* ── Headings del feedback (## secciones de Claude) ── */
        [data-testid="stMarkdownContainer"] h2 {
            font-size: 1.1rem;
            font-weight: 600;
            color: #E8E8E8;
            margin-top: 1.4rem;
            margin-bottom: 0.4rem;
        }

        /* ── Listas del feedback con sangría limpia ── */
        [data-testid="stMarkdownContainer"] ul {
            padding-left: 1.2rem;
            line-height: 1.75;
        }

        /* ── Cursiva del feedback (limitaciones) en gris suave ── */
        [data-testid="stMarkdownContainer"] em {
            color: #999;
            font-style: italic;
        }

        /* ── Separador horizontal del feedback ── */
        [data-testid="stMarkdownContainer"] hr {
            border-color: #2A2D38;
            margin: 1rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
