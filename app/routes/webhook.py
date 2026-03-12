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

    try:
        mensaje = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
        telefono = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]

    except:
        return {"status": "no message"}

    print("Mensaje recibido:", mensaje)

    movimiento = interpretar_gasto(mensaje)

    print("Movimiento interpretado:", movimiento)

    guardar_movimiento(movimiento)

    enviar_respuesta(telefono, movimiento)

    return {"status": "ok"}


def enviar_respuesta(telefono, movimiento):

    url = f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    mensaje = f"✅ Movimiento guardado\n{movimiento['descripcion']} - ${movimiento['monto']}"

    payload = {
        "messaging_product": "whatsapp",
        "to": telefono,
        "type": "text",
        "text": {
            "body": mensaje
        }
    }

    r = requests.post(url, headers=headers, json=payload)

    print("WHATSAPP RESPONSE:", r.status_code)
    print(r.text)