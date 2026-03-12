from fastapi import APIRouter, Request
import requests
import os

from app.services.ai_parser import interpretar_gasto
from app.services.movimientos_service import guardar_movimiento

router = APIRouter()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("PHONE_ID")

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")


@router.get("/webhook")
async def verify_webhook(request: Request):

    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)

    return {"error": "verification failed"}


@router.post("/webhook")
async def webhook(request: Request):

    data = await request.json()

    print("Webhook recibido:", data)

    try:
        value = data["entry"][0]["changes"][0]["value"]

        # Si no es un mensaje, ignorar
        if "messages" not in value:
            return {"status": "evento ignorado"}

        mensaje = value["messages"][0]["text"]["body"]
        telefono = value["messages"][0]["from"]

    except Exception as e:
        print("Error leyendo mensaje:", e)
        return {"status": "error parsing"}

    print("Mensaje recibido:", mensaje)

    respuesta = interpretar_gasto(mensaje)

    print("Respuesta IA:", respuesta)

    if respuesta["accion"] == "preguntar":
        enviar_respuesta(telefono, respuesta["pregunta"])
        return {"status": "pregunta enviada"}

    if respuesta["accion"] == "registrar":

        guardar_movimiento(respuesta)

        mensaje_confirmacion = f"""
    ✅ Movimiento registrado

    {respuesta["descripcion"]}
    ${respuesta["monto"]}
    """

        enviar_respuesta(telefono, mensaje_confirmacion)

        return {"status": "movimiento guardado"}


def enviar_respuesta(telefono, mensaje):

    url = f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": telefono,
        "type": "text",
        "text": {
            "body": mensaje
        }
    }

    requests.post(url, headers=headers, json=payload)