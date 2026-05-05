"""
test_conexion.py — Verifica que la API key de Anthropic funciona correctamente.

Cómo usar:
  1. Asegúrate de haber pegado tu API key en el archivo .env (ver instrucciones abajo)
  2. Desde la raíz del proyecto, corre: venv\Scripts\python src/feedback/test_conexion.py

El script hace una pregunta simple a Claude y muestra la respuesta.
Si funciona, verás: "✓ Conexión exitosa."
"""

import os
import sys

# python-dotenv lee el archivo .env y carga las variables de entorno
from dotenv import load_dotenv
import anthropic

def probar_conexion():
    # Cargar variables desde el archivo .env (busca en la raíz del proyecto)
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")

    # Verificar que la key existe y no está vacía
    if not api_key or api_key.strip() == "" or api_key == "tu_api_key_aqui_no_compartir":
        print("ERROR: No encontré tu API key en el archivo .env")
        print()
        print("Pasos para solucionarlo:")
        print("  1. Abre el archivo .env en la raíz del proyecto")
        print("  2. Reemplaza la línea con tu key real:")
        print("     ANTHROPIC_API_KEY=sk-ant-...")
        print("  3. Guarda el archivo y vuelve a correr este script")
        sys.exit(1)

    print("API key encontrada. Probando conexión con Claude...")
    print()

    try:
        cliente = anthropic.Anthropic(api_key=api_key)

        respuesta = cliente.messages.create(
            model="claude-haiku-4-5-20251001",  # modelo barato para pruebas
            max_tokens=50,
            messages=[
                {
                    "role": "user",
                    "content": "Responde solo con la palabra OK si me estás escuchando."
                }
            ]
        )

        texto = respuesta.content[0].text
        print(f"Respuesta de Claude: {texto}")
        print()
        print("✓ Conexión exitosa. La API key funciona correctamente.")

    except anthropic.AuthenticationError:
        print("ERROR: La API key es inválida o fue revocada.")
        print("Verifica que copiaste la key completa desde console.anthropic.com")
        sys.exit(1)

    except anthropic.PermissionDeniedError:
        print("ERROR: Tu API key no tiene permisos para usar este modelo.")
        print("Verifica que tu cuenta tiene créditos disponibles en console.anthropic.com")
        sys.exit(1)

    except anthropic.APIConnectionError:
        print("ERROR: No hay conexión a internet o el servidor no responde.")
        print("Verifica tu conexión a internet e inténtalo de nuevo.")
        sys.exit(1)

    except anthropic.RateLimitError:
        print("ERROR: Demasiadas solicitudes. Espera unos segundos e inténtalo de nuevo.")
        sys.exit(1)

    except anthropic.APIStatusError as e:
        print(f"ERROR inesperado de la API (código {e.status_code}): {e.message}")
        sys.exit(1)


if __name__ == "__main__":
    probar_conexion()
