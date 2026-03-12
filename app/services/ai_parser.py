from openai import OpenAI
import os
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def interpretar_gasto(texto):

    prompt = f"""
    Eres un asistente financiero que registra movimientos de dinero.

    Debes analizar el mensaje del usuario y extraer:

    tipo: ingreso o gasto
    descripcion
    monto
    categoria
    fecha

    Reglas importantes:

    - Si el usuario compra algo → gasto
    - Si el usuario recibe dinero → ingreso
    - Si no estás seguro del tipo → marca "duda"

    Ejemplos:

    Mensaje: "compre sushi 12000"
    Respuesta:
    {{
    "tipo": "gasto",
    "descripcion": "sushi",
    "monto": 12000,
    "categoria": "comida",
    "fecha": "hoy"
    }}

    Mensaje: "me pagaron sueldo 900000"
    Respuesta:
    {{
    "tipo": "ingreso",
    "descripcion": "sueldo",
    "monto": 900000,
    "categoria": "sueldo",
    "fecha": "hoy"
    }}

    Mensaje: "transferencia 50000"
    Respuesta:
    {{
    "tipo": "duda",
    "descripcion": "transferencia",
    "monto": 50000,
    "categoria": "otros",
    "fecha": "hoy"
    }}

    Mensaje del usuario:
    {texto}

    Responde SOLO en JSON válido con esta estructura:

    {{
    "tipo": "",
    "descripcion": "",
    "monto": 0,
    "categoria": "",
    "fecha": ""
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Eres un agente financiero."},
            {"role": "user", "content": prompt}
        ]
    )

    contenido = response.choices[0].message.content

    return json.loads(contenido)