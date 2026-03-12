# AGENT CONTEXT

## Project Overview

This project is an AI financial assistant that runs on WhatsApp.

The system allows users to register personal financial movements (expenses and income) by sending natural language messages through WhatsApp.

The assistant interprets messages using OpenAI and stores the resulting financial movements in Supabase.

Example user message:

"compre sushi 12000"

Result:

{
  "tipo": "gasto",
  "descripcion": "sushi",
  "monto": 12000,
  "categoria": "comida",
  "fecha": "hoy"
}

The system then stores the movement and sends a confirmation message to the user.

---

# Architecture

WhatsApp → FastAPI Webhook → OpenAI Parser → Supabase → WhatsApp Response

Components:

- WhatsApp Cloud API: messaging interface
- FastAPI: backend server
- OpenAI: natural language interpretation
- Supabase: database
- Railway: production hosting

---

# Project Structure

agenteFinanciero/

app/
    routes/
        webhook.py
        Handles WhatsApp webhook events

    services/
        ai_parser.py
        Uses OpenAI to interpret financial messages

        movimientos_service.py
        Stores financial movements in Supabase

    database/
        supabase_client.py
        Supabase connection

main.py
FastAPI application entry point

requirements.txt
Python dependencies

---

# Webhook Behavior

The webhook receives events from WhatsApp.

Important: WhatsApp sends multiple types of events.

messages → user message  
statuses → message delivery events

The system must only process events containing:

"value.messages"

Statuses must be ignored.

---

# AI Agent Responsibilities

The AI must analyze the user message and return a JSON response.

Supported actions:

registrar  
A valid financial movement was detected and should be stored.

preguntar  
Information is missing and the assistant should ask the user.

conversar  
The message is conversational and not a financial movement.

Example outputs:

Registrar:

{
"accion": "registrar",
"tipo": "gasto",
"descripcion": "sushi",
"monto": 12000,
"categoria": "comida",
"fecha": "hoy"
}

Preguntar:

{
"accion": "preguntar",
"pregunta": "¿Podrías indicar el monto?"
}

Conversar:

{
"accion": "conversar",
"respuesta": "Puedo ayudarte a registrar gastos o ingresos."
}

---

# Financial Rules

User buys something → gasto  
User receives money → ingreso  

The agent must ensure that a movement contains at least:

tipo  
descripcion  
monto  

If information is missing, the assistant must ask a question.

---

# Database

Supabase table: movimientos

Fields:

tipo  
descripcion  
monto  
categoria  
fecha

The service `movimientos_service.py` handles inserts.

---

# Local Development

Run the server:

uvicorn app.main:app --reload

Webhook testing uses ngrok.

---

# Production

Hosted on Railway.

Deployment pipeline:

git push → Railway build → automatic deploy

---

# Future Improvements

The following features may be added in the future:

conversation memory  
expense queries (e.g. "cuanto gaste hoy")  
monthly financial summaries  
transaction editing