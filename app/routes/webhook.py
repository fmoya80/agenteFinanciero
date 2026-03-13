from fastapi import APIRouter, Request
import requests
import os

from app.services.ai_parser import interpretar_gasto
from app.services.movimientos_service import (
    guardar_movimiento,
    sum_movimientos_by_period,
    sum_movimientos_by_period_and_category,
    sum_movimientos_grouped_by_category,
)
from app.services.categories_service import (
    create_category,
    find_user_category_by_name,
    get_user_categories,
    get_or_create_default_category,
    resolve_category_for_user,
)
from app.services.periods_service import period_label, resolve_period_to_range
from app.services.users_service import get_or_create_user

router = APIRouter()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("PHONE_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

HELP_MESSAGE = (
    "Te puedo ayudar con tu control financiero:\n"
    "1) Registrar gastos\n"
    "2) Registrar ingresos\n"
    "3) Consultar gastos por periodo\n"
    "4) Crear categorias personalizadas\n"
    "5) Organizar movimientos por categorias\n\n"
    "Ejemplos de mensajes:\n"
    "- 'gaste 12000 en sushi'\n"
    "- 'me pagaron 950000 de sueldo'\n"
    "- 'cuanto gaste esta semana?'\n"
    "- 'crear categoria Transporte: uber, metro, bus'\n"
    "- 'gaste 8000 en bencina (transporte)'"
)

WELCOME_MESSAGE = (
    "Hola, soy tu asistente financiero por WhatsApp. "
    "Si quieres, escribe 'que puedes hacer' y te muestro ejemplos."
)

CLARIFICATION_MESSAGE_DEFAULT = (
    "Necesito un poco mas de detalle para ayudarte. "
    "Puedes escribir monto + descripcion, por ejemplo: 'gasto 12000 en comida'."
)


def _format_clp(value: float) -> str:
    rounded = int(round(value))
    return f"{rounded:,}".replace(",", ".")


def _map_category_names(categorias_usuario: list[dict]) -> dict[str, str]:
    return {
        (cat.get("id") or "").strip(): (cat.get("nombre") or "Sin categoria").strip()
        for cat in categorias_usuario
        if (cat.get("id") or "").strip()
    }


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
        if "messages" not in value:
            return {"status": "evento ignorado"}

        msg = value["messages"][0]
        if msg.get("type") != "text":
            return {"status": "mensaje no-texto ignorado"}

        mensaje = msg["text"]["body"]
        telefono = msg["from"]
        contactos = value.get("contacts", [])
        display_name = None
        if contactos:
            display_name = (contactos[0].get("profile") or {}).get("name")
    except Exception as e:
        print("Error leyendo mensaje:", e)
        return {"status": "error parsing webhook"}

    print("Mensaje recibido:", mensaje)

    try:
        user = get_or_create_user(telefono, display_name=display_name)
        user_id = user["id"]
        print("Usuario resuelto para webhook:", {"telefono": telefono, "user_id": user_id})
        get_or_create_default_category(user_id)
        categorias_usuario = get_user_categories(user_id)
    except Exception as e:
        print("Error resolviendo usuario:", e)
        enviar_respuesta(telefono, "No pude identificar tu usuario. Intenta nuevamente.")
        return {"status": "error user"}

    try:
        respuesta = interpretar_gasto(mensaje, categorias_usuario=categorias_usuario)
    except Exception as e:
        print("Error interpretando mensaje:", e)
        enviar_respuesta(telefono, "No pude interpretar el mensaje. Escribe algo como: 'gasto 12000 en comida'.")
        return {"status": "error parser"}

    print("Respuesta IA:", respuesta)

    intent = (respuesta.get("intent") or "").strip().lower()

    if intent == "crear_categoria":
        nombre_categoria = (respuesta.get("categoria_nueva_nombre") or "").strip()
        descripcion_categoria = (respuesta.get("categoria_nueva_descripcion") or "").strip()
        clarification_message = (respuesta.get("clarification_message") or "").strip()

        if not nombre_categoria or not descripcion_categoria:
            reply_text = (
                clarification_message
                or "Para crear una categoria necesito nombre y descripcion. Ejemplo: 'crear categoria Transporte: uber, metro, bus'."
            )
            enviar_respuesta(telefono, reply_text)
            return {"status": "crear_categoria_falta_info"}

        try:
            categoria_creada = create_category(user_id, nombre_categoria, descripcion_categoria)
            print("Resultado create_category:", categoria_creada)
            if categoria_creada:
                enviar_respuesta(
                    telefono,
                    (
                        "Categoria creada correctamente:\n"
                        f"- Nombre: {categoria_creada.get('nombre')}\n"
                        f"- Descripcion: {categoria_creada.get('descripcion') or ''}"
                    ),
                )
                return {"status": "categoria_creada"}

            enviar_respuesta(
                telefono,
                "No pude confirmar la creacion de la categoria en Supabase. Intenta nuevamente."
            )
            return {"status": "categoria_no_confirmada"}
        except Exception as e:
            print("Error creando categoria:", e)
            enviar_respuesta(
                telefono,
                "Hubo un problema al crear la categoria. Revisa si ya existe y vuelve a intentarlo."
            )
            return {"status": "error_crear_categoria"}

    if intent in {"consultar_movimientos", "consultar_o_pregunta"} and (respuesta.get("periodo") or "").strip():
        periodo = (respuesta.get("periodo") or "").strip().lower()
        tipo_consulta = (respuesta.get("tipo") or "gasto").strip().lower()
        query_scope = (respuesta.get("query_scope") or "total_general").strip().lower()
        categoria_consulta = (respuesta.get("categoria_consulta") or "").strip()
        clarification_message = (respuesta.get("clarification_message") or "").strip()

        if tipo_consulta not in {"gasto", "ingreso"}:
            tipo_consulta = "gasto"
        if query_scope not in {"total_general", "total_categoria", "desglose_categorias"}:
            query_scope = "total_general"

        try:
            fecha_inicio, fecha_fin, periodo_normalizado = resolve_period_to_range(periodo)
        except ValueError:
            enviar_respuesta(
                telefono,
                clarification_message or "No reconoci ese periodo. Prueba con: hoy, esta_semana, este_mes o ultimos_7_dias."
            )
            return {"status": "consulta_periodo_invalido"}

        periodo_texto = period_label(periodo_normalizado)

        try:
            if query_scope == "desglose_categorias":
                grouped = sum_movimientos_grouped_by_category(user_id, tipo_consulta, fecha_inicio, fecha_fin)
                grouped = [x for x in grouped if x.get("total", 0) > 0]
                if not grouped:
                    noun = "gastos" if tipo_consulta == "gasto" else "ingresos"
                    enviar_respuesta(telefono, f"No encontre {noun} registrados en {periodo_texto}.")
                    return {"status": "consulta_sin_resultados"}

                names_map = _map_category_names(categorias_usuario)
                header = (
                    f"Este es tu desglose de gastos por categoria en {periodo_texto}:\n"
                    if tipo_consulta == "gasto"
                    else f"Este es tu desglose de ingresos por categoria en {periodo_texto}:\n"
                )
                lines = []
                for item in grouped:
                    cat_id = item.get("categoria_id") or ""
                    cat_name = names_map.get(cat_id, "Sin categoria")
                    total_txt = _format_clp(item.get("total", 0.0))
                    lines.append(f"- {cat_name}: ${total_txt} CLP")

                enviar_respuesta(telefono, header + "\n".join(lines))
                return {"status": "consulta_desglose_ok"}

            if query_scope == "total_categoria":
                categoria_obj = find_user_category_by_name(user_id, categoria_consulta, categorias_usuario)
                if not categoria_obj:
                    sugeridas = ", ".join([
                        (c.get("nombre") or "").strip()
                        for c in categorias_usuario[:6]
                        if (c.get("nombre") or "").strip()
                    ])
                    msg = (
                        f"No encontre la categoria '{categoria_consulta}' en tus categorias."
                        + (f" Puedes usar: {sugeridas}." if sugeridas else "")
                    )
                    enviar_respuesta(telefono, msg)
                    return {"status": "consulta_categoria_no_encontrada"}

                total = sum_movimientos_by_period_and_category(
                    user_id=user_id,
                    tipo=tipo_consulta,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    categoria_id=categoria_obj["id"],
                )
                if total <= 0:
                    noun = "gastos" if tipo_consulta == "gasto" else "ingresos"
                    enviar_respuesta(
                        telefono,
                        f"No encontre {noun} en {categoria_obj.get('nombre')} durante {periodo_texto}.",
                    )
                    return {"status": "consulta_sin_resultados"}

                total_txt = _format_clp(total)
                if tipo_consulta == "gasto":
                    reply_text = f"Gastaste ${total_txt} CLP en {categoria_obj.get('nombre')} durante {periodo_texto}."
                else:
                    reply_text = f"Recibiste ${total_txt} CLP en {categoria_obj.get('nombre')} durante {periodo_texto}."
                enviar_respuesta(telefono, reply_text)
                return {"status": "consulta_categoria_ok"}

            total = sum_movimientos_by_period(user_id, tipo_consulta, fecha_inicio, fecha_fin)
            if total <= 0:
                noun = "gastos" if tipo_consulta == "gasto" else "ingresos"
                enviar_respuesta(telefono, f"No encontre {noun} registrados en {periodo_texto}.")
                return {"status": "consulta_sin_resultados"}

            total_txt = _format_clp(total)
            if tipo_consulta == "gasto":
                if periodo_normalizado == "este_mes":
                    reply_text = f"Llevas gastados ${total_txt} CLP este mes."
                else:
                    reply_text = f"Gastaste ${total_txt} CLP en {periodo_texto} :)"
            else:
                if periodo_normalizado == "este_mes":
                    reply_text = f"Llevas ingresados ${total_txt} CLP este mes."
                else:
                    reply_text = f"Recibiste ${total_txt} CLP en {periodo_texto}."

            enviar_respuesta(telefono, reply_text)
            return {"status": "consulta_ok"}
        except Exception as e:
            print("Error consultando movimientos por periodo:", e)
            enviar_respuesta(telefono, "Hubo un problema al consultar tus movimientos. Intenta nuevamente.")
            return {"status": "error_consulta"}

    if not respuesta.get("should_save", False):
        clarification_message = (respuesta.get("clarification_message") or "").strip()
        if clarification_message:
            reply_text = clarification_message
            status = "mensaje_parser_enviado"
        elif intent == "ayuda_capacidades":
            reply_text = HELP_MESSAGE
            status = "ayuda_enviada"
        elif intent == "conversacional":
            reply_text = WELCOME_MESSAGE
            status = "bienvenida_enviada"
        elif respuesta.get("needs_clarification", False):
            reply_text = CLARIFICATION_MESSAGE_DEFAULT
            status = "aclaracion_solicitada"
        else:
            reply_text = HELP_MESSAGE
            status = "no_registrable"

        enviar_respuesta(telefono, reply_text)
        return {"status": status}

    try:
        categoria_resuelta = resolve_category_for_user(
            user_id=user_id,
            descripcion_movimiento=respuesta.get("descripcion", ""),
            categorias_disponibles=categorias_usuario,
            categoria_sugerida=respuesta.get("categoria"),
        )
        _, movimiento_valido = guardar_movimiento(respuesta, user_id, categoria_resuelta)
    except ValueError as e:
        enviar_respuesta(telefono, f"No pude registrar el movimiento: {str(e)}")
        return {"status": "movimiento invalido"}
    except Exception as e:
        print("Error guardando movimiento:", e)
        enviar_respuesta(telefono, "Hubo un problema al guardar en Supabase. Intenta nuevamente.")
        return {"status": "error guardado"}

    mensaje_confirmacion = (
        "Movimiento registrado:\n"
        f"{movimiento_valido['tipo']} - {movimiento_valido['descripcion']}\n"
        f"${movimiento_valido['monto']}\n"
        f"Categoria: {movimiento_valido['categoria']}\n"
        f"Fecha: {movimiento_valido['fecha']}"
    )

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
        "text": {"body": str(mensaje)}
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if not response.ok:
            print("Error enviando a WhatsApp:", response.status_code, response.text)
    except Exception as e:
        print("Excepcion enviando a WhatsApp:", e)
