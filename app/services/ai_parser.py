from openai import OpenAI
import os
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def interpretar_gasto(texto):

    prompt = f"""
    Eres un asistente financiero que registra movimientos de dinero en una base de datos.
    Recuerda ser cordial y cada tanto enviar emojis.

    Tu tarea es analizar el mensaje del usuario y extraer información de un movimiento financiero.

    Campos necesarios para registrar un movimiento:

    - tipo: ingreso o gasto
    - descripcion
    - monto
    - categoria
    - fecha

    Reglas importantes:

    1. Si el usuario compra algo → gasto
    2. Si el usuario recibe dinero → ingreso
    3. Si no estás seguro del tipo → "duda"
    4. NUNCA inventes un monto
    5. Si falta el monto debes pedirlo al usuario
    6. Si falta información crítica debes continuar la conversación

    Comportamiento:

    Si tienes toda la información → accion = "registrar"

    Si falta información → accion = "preguntar"

    Ejemplos:

    Usuario: "compre sushi 12000"

    Respuesta:
    {{
    "accion": "registrar",
    "tipo": "gasto",
    "descripcion": "sushi",
    "monto": 12000,
    "categoria": "comida",
    "fecha": "hoy",
    "pregunta": ""
    }}

    Usuario: "compre sushi"

    Respuesta:
    {{
    "accion": "preguntar",
    "tipo": "gasto",
    "descripcion": "sushi",
    "monto": null,
    "categoria": "comida",
    "fecha": "hoy",
    "pregunta": "¿Cuánto gastaste en sushi?"
    }}

    Usuario: "me pagaron sueldo"

    Respuesta:
    {{
    "accion": "preguntar",
    "tipo": "ingreso",
    "descripcion": "sueldo",
    "monto": null,
    "categoria": "sueldo",
    "fecha": "hoy",
    "pregunta": "¿Cuánto fue el sueldo que recibiste?"
    }}

    Mensaje del usuario:
    {texto}

    Responde SOLO en JSON válido con esta estructura:

    {{
    "accion": "",
    "tipo": "",
    "descripcion": "",
    "monto": null,
    "categoria": "",
    "fecha": "",
    "pregunta": ""
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