# -*- coding: utf-8 -*-

# ----------------------------------------------------------------------------------
# app.py - Conexión Directa a Telegram con OpenAI
# ----------------------------------------------------------------------------------
# Este código utiliza la librería python-telegram-bot para una conexión directa,
# eliminando la necesidad de un intermediario como Twilio.
# ----------------------------------------------------------------------------------

# --- Importación de Librerías ---
import os
import asyncio
from flask import Flask, request, Response
import telegram
import openai

# --- Configuración Inicial ---

app = Flask(__name__)

# --- Claves y Tokens (Configuración Segura) ---

# Token de tu bot de Telegram (obtenido de BotFather)
# Configúralo como una Variable de Entorno en Render: TELEGRAM_TOKEN
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

# Clave de la API de OpenAI
# Configúrala como una Variable de Entorno en Render: OPENAI_API_KEY
openai.api_key = os.environ.get('OPENAI_API_KEY')

# --- "Cerebro" del Asistente Virtual (System Prompt) ---
# Este es el mismo prompt que ya diseñamos para la clínica.
SYSTEM_PROMPT = """
Rol: Eres "Salud-Bot", el asistente virtual oficial de la "Clínica Salud Integral". Tu personalidad es amable, empática, eficiente y extremadamente profesional. Tu misión es facilitar la gestión de citas y resolver dudas administrativas.

Tarea Principal: Tu objetivo es asistir a los pacientes en las siguientes tareas:
1.  Agendar Citas: Guía al usuario paso a paso para agendar una cita. Pregunta por la especialidad (Medicina General, Pediatría, Cardiología), muestra médicos y horarios ficticios, y confirma la cita pidiendo nombre completo y DNI.
2.  Consultar y Cancelar Citas: Permite a los usuarios consultar sus citas programadas o cancelarlas usando su DNI como identificador. Debes informar que la cancelación debe ser con 24 horas de antelación.
3.  Responder Preguntas Frecuentes (FAQs):
    - Horarios de atención: Lunes a Sábado de 8:00 am a 7:00 pm.
    - Dirección: Avenida Principal 123, Distrito de Miraflores, Lima.
    - Seguros aceptados: Pacífico, Rimac y Mapfre.
    - Teléfono de contacto: (01) 555-1234.

Reglas y Limitaciones Estrictas e Inquebrantables:
-   NUNCA, bajo ninguna circunstancia, ofrezcas consejos médicos, diagnósticos, interpretaciones de síntomas o información sobre medicamentos. Si un usuario pregunta por temas médicos, DEBES responder exclusivamente con: "Como asistente virtual, no estoy calificado para dar consejos médicos. Por favor, agenda una cita para que un especialista pueda ayudarte".
-   Sé siempre cortés y utiliza un lenguaje claro, sencillo y profesional.
-   Si te preguntan algo fuera de tu alcance (temas no relacionados con la Clínica Salud Integral), responde con: "Mi función es ayudarte con los servicios de la Clínica Salud Integral. ¿Cómo puedo asistirte con eso?".
"""

def generar_respuesta_con_ia(mensaje_usuario: str) -> str:
    """
    Envía el mensaje del usuario a la API de OpenAI y devuelve la respuesta.
    """
    if not openai.api_key:
        return "Error de configuración: La clave de API de OpenAI no está configurada."
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": mensaje_usuario}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error al contactar con OpenAI: {e}")
        return "Lo siento, estoy teniendo problemas técnicos en este momento."

# --- Webhook para Recibir Mensajes de Telegram ---
# Esta es la ruta que le daremos a Telegram para que nos envíe las actualizaciones.
@app.route("/webhook", methods=['POST'])
def telegram_webhook():
    """
    Procesa las actualizaciones (mensajes) que envía Telegram.
    """
    update_data = request.get_json()
    print("Datos recibidos de Telegram:", update_data)

    if 'message' in update_data:
        chat_id = update_data['message']['chat']['id']
        mensaje_recibido = update_data['message'].get('text', '')

        if mensaje_recibido:
            # Genera la respuesta con IA
            respuesta_ia = generar_respuesta_con_ia(mensaje_recibido)

            # Envía la respuesta de vuelta al usuario usando la librería de Telegram
            # Usamos asyncio para manejar la operación asíncrona de forma simple
            asyncio.run(enviar_mensaje_telegram(chat_id, respuesta_ia))

    # Telegram espera una respuesta HTTP 200 OK para saber que recibimos el mensaje.
    return Response(status=200)

async def enviar_mensaje_telegram(chat_id, texto):
    """
    Función asíncrona para enviar un mensaje a un chat de Telegram.
    """
    if not TELEGRAM_TOKEN:
        print("Error: El token de Telegram no está configurado.")
        return

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=chat_id, text=texto)

# Punto de entrada para Gunicorn en Render
if __name__ != '__main__':
    # Esta configuración es para asegurar que Gunicorn pueda encontrar la app
    gunicorn_app = app