# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# app.py - Chatbot para Clínica usando Telegram, Twilio y OpenAI (ChatGPT)
# ---------------------------------------------------------------------------
# Este archivo contiene el código para un servidor web Flask que actúa como
# webhook para Twilio, conectando un bot de Telegram con la API de OpenAI.
#
# Funcionalidad:
# 1. Recibe mensajes de usuarios de Telegram a través de Twilio.
# 2. Envía estos mensajes a la API de OpenAI para generar una respuesta inteligente.
# 3. Devuelve la respuesta de la IA al usuario a través de Twilio.
# ---------------------------------------------------------------------------

# --- Importación de Librerías Necesarias ---
import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import openai

# --- Configuración Inicial de la Aplicación ---

# Inicializa la aplicación Flask
app = Flask(__name__)

# Configura la clave de la API de OpenAI de forma segura.
# ¡IMPORTANTE! No escribas tu clave aquí.
# Debes configurarla como una "Variable de Entorno" en tu plataforma de despliegue (Render, PythonAnywhere, etc.).
# Nombre de la variable: OPENAI_API_KEY
try:
    openai.api_key = os.environ.get('OPENAI_API_KEY')
    if not openai.api_key:
        print("ADVERTENCIA: La variable de entorno OPENAI_API_KEY no está configurada.")
except Exception as e:
    print(f"Error al configurar la clave de OpenAI: {e}")


# --- "Cerebro" del Asistente Virtual (System Prompt) ---
# Este es el contexto principal que define la personalidad, las tareas y
# las reglas de nuestro asistente de IA. Es la parte más importante para
# guiar el comportamiento del modelo.
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
-   Al confirmar una cita, siempre presenta un resumen claro: "Perfecto. Su cita ha sido agendada para el [Día] a las [Hora] con el/la Dr./Dra. [Nombre del Médico] en la especialidad de [Especialidad]. ¿Es correcto?".
"""

def generar_respuesta_con_ia(mensaje_usuario: str) -> str:
    """
    Envía el mensaje del usuario a la API de OpenAI junto con el contexto del sistema
    y devuelve la respuesta generada por la inteligencia artificial.

    Args:
        mensaje_usuario: El texto del mensaje enviado por el usuario.

    Returns:
        La respuesta generada por el modelo de OpenAI.
    """
    if not openai.api_key:
        return "Error de configuración: La clave de API de OpenAI no ha sido establecida. Por favor, contacte al administrador."

    try:
        # Realiza la llamada a la API de Chat Completions de OpenAI
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Modelo rápido y eficiente para chatbots
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": mensaje_usuario}
            ],
            temperature=0.7,  # Creatividad moderada para respuestas naturales pero consistentes
            max_tokens=250    # Límite de longitud para evitar respuestas demasiado largas
        )
        # Extrae el contenido del mensaje de la respuesta
        return response.choices[0].message.content.strip()
    except Exception as e:
        # Manejo de errores en caso de que la API de OpenAI falle
        print(f"ERROR: No se pudo conectar con la API de OpenAI. Detalles: {e}")
        return "Lo siento, estoy experimentando problemas técnicos en este momento. Por favor, intenta de nuevo en unos minutos."


# --- Webhook para Recibir Mensajes de Telegram vía Twilio ---
# Esta es la ruta que configurarás en la consola de Twilio.
# Twilio reenviará todos los mensajes que lleguen a tu bot de Telegram a esta URL.
@app.route("/telegram", methods=['POST'])
def telegram_webhook():
    """
    Procesa los mensajes entrantes de Telegram.
    """
    # Extrae el cuerpo del mensaje del usuario de la petición de Twilio
    mensaje_recibido = request.values.get('Body', '').strip()
    print(f"Mensaje recibido de Telegram: '{mensaje_recibido}'")

    # Prepara el objeto de respuesta de Twilio
    respuesta_twilio = MessagingResponse()

    # Si el mensaje está vacío, no hace falta procesarlo
    if not mensaje_recibido:
        respuesta_twilio.message("Por favor, envía un mensaje de texto.")
        return str(respuesta_twilio)

    # 1. Obtiene la respuesta inteligente de la función de OpenAI
    respuesta_ia = generar_respuesta_con_ia(mensaje_recibido)
    print(f"Respuesta generada por IA: '{respuesta_ia}'")

    # 2. Añade la respuesta de la IA al objeto de respuesta de Twilio
    respuesta_twilio.message(respuesta_ia)

    # 3. Devuelve la respuesta en formato TwiML para que Twilio la envíe a Telegram
    return str(respuesta_twilio)


# --- Punto de Entrada para Ejecutar la Aplicación ---
# Este bloque se ejecuta solo si corres el archivo directamente (ej. `python app.py`)
# No es utilizado por Gunicorn en producción, pero es útil para pruebas locales.
if __name__ == "__main__":
    # El modo debug es útil para desarrollo, pero debe estar en False en producción.
    app.run(port=5000, debug=True)
