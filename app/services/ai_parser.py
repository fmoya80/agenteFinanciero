from openai import OpenAI
import os
import json
import traceback

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _safe_log(label: str, value) -> None:
    text = str(value)
    try:
        print(label, text)
    except UnicodeEncodeError:
        safe_text = text.encode("ascii", errors="backslashreplace").decode("ascii")
        print(label, safe_text)


def _prompt_parser(texto: str, categorias_usuario: list[dict]) -> str:
    if categorias_usuario:
        categorias_texto = "\n".join(
            [
                f'- nombre: "{(cat.get("nombre") or "").strip()}" | descripcion: "{(cat.get("descripcion") or "").strip()}"'
                for cat in categorias_usuario
                if (cat.get("nombre") or "").strip()
            ]
        )
    else:
        categorias_texto = '- nombre: "otros" | descripcion: "Categoria por defecto"'

    return f"""
Eres un parser de movimientos financieros para WhatsApp.

Objetivo:
- Determinar si un mensaje representa un movimiento registrable en Supabase.
- Nunca registrar consultas, preguntas, saludos o mensajes ambiguos.

Reglas obligatorias:
1. Solo registrar si hay intencion clara de gasto o ingreso.
2. Solo registrar si hay monto numerico explicito y mayor a 0.
3. Nunca inventar monto, descripcion, tipo ni fecha.
4. Si falta monto o es ambiguo, no registrar y pedir aclaracion.
5. Si el mensaje es consulta/pregunta/conversacion, no registrar.
6. Categoria debe elegirse desde las categorias del usuario cuando exista match.
7. Usa nombre + descripcion de categorias para clasificar mejor.
8. Si no hay match claro con categorias del usuario, usar "otros".
9. No inventar categorias fuera de la lista entregada por el sistema.
10. Si el usuario expresa intencion de crear una categoria nueva, usar intent "crear_categoria".
11. Si falta nombre o descripcion para crear categoria, pedir aclaracion.
12. Persistencia es en Supabase (no Google Sheets).
13. Devuelve solo JSON valido.
14. Si el usuario pregunta que puedes hacer, en que ayudas, como funcionas o que puede escribirte, usa intent "ayuda_capacidades" y responde con un mensaje claro y amigable.
15. La respuesta de ayuda debe incluir: registrar gastos, registrar ingresos, consultar gastos por periodo, crear categorias personalizadas y organizar movimientos por categorias.
16. Si el mensaje consulta totales en el tiempo, usar intent "consultar_movimientos" y detectar periodo + tipo.
17. Periodos soportados para consultas: hoy, ayer, esta_semana, semana_pasada, este_mes, mes_pasado, ultimos_7_dias, ultimos_30_dias.
18. Para consultas, tipo debe ser "gasto" o "ingreso" si se puede inferir.
19. Distingue consultas:
   - total_general: total por periodo sin categoria puntual.
   - total_categoria: total por periodo filtrado por una categoria puntual.
   - desglose_categorias: lista de categorias con sus totales para el periodo.

Categorias disponibles del usuario:
{categorias_texto}

Ejemplos que SI registran:
- "compre sushi 12000"
- "me pagaron 450000"
- "uber 8500"

Ejemplos que NO registran:
- "cuanto gaste hoy"
- "tengo gastos esta semana?"
- "compre sushi"
- "hola"
- "anota algo"
- "ayer gaste"

Devuelve SOLO JSON valido con este contrato exacto:
{{
  "intent": "registrar_gasto | registrar_ingreso | consultar_movimientos | consultar_o_pregunta | crear_categoria | ayuda_capacidades | mensaje_ambiguo | conversacional",
  "should_save": false,
  "needs_clarification": false,
  "clarification_message": "",
  "tipo": null,
  "descripcion": "",
  "monto": null,
  "periodo": "",
  "query_scope": "",
  "categoria_consulta": "",
  "categoria": "",
  "fecha": null,
  "categoria_nueva_nombre": "",
  "categoria_nueva_descripcion": ""
}}

Reglas del contrato:
- intent=registrar_gasto -> tipo="gasto"
- intent=registrar_ingreso -> tipo="ingreso"
- should_save=true solo si intent es registrar_* y monto>0 con descripcion no vacia
- Si should_save=true, categoria debe ser una de las categorias disponibles del usuario o "otros"
- intent=crear_categoria -> should_save=false (no registrar movimiento)
- intent=crear_categoria y falta nombre o descripcion -> needs_clarification=true
- intent=ayuda_capacidades -> should_save=false y clarification_message con capacidades y ejemplos
- intent=consultar_movimientos -> should_save=false y debe incluir periodo; tipo preferido: gasto o ingreso
- Si intent=consultar_movimientos:
  - query_scope debe ser total_general | total_categoria | desglose_categorias
  - en total_categoria debes completar categoria_consulta
- Si should_save=false y falta monto/claridad -> needs_clarification=true con pregunta concreta
- Si es consulta o conversacional -> needs_clarification=false y clarification_message puede sugerir que envies un gasto/ingreso con monto

Siempre usa el emoji más ad hoc para la categoria.
Recuerda usar emojis en algunos mensajes para ser mas cercano.


Mensaje del usuario:
{texto}
"""


def interpretar_gasto(texto: str, categorias_usuario: list[dict] | None = None) -> dict:
    _safe_log("[ai_parser] mensaje_original:", texto)
    categorias_normalizadas = []
    nombres_vistos = set()
    for cat in categorias_usuario or []:
        nombre = (cat.get("nombre") or "").strip()
        if not nombre:
            continue
        key = nombre.lower()
        if key in nombres_vistos:
            continue
        nombres_vistos.add(key)
        categorias_normalizadas.append(
            {"nombre": nombre, "descripcion": (cat.get("descripcion") or "").strip()}
        )

    if "otros" not in nombres_vistos:
        categorias_normalizadas.append({"nombre": "otros", "descripcion": "Categoria por defecto"})

    prompt_final = _prompt_parser(texto, categorias_normalizadas)
    print("[ai_parser] prompt_final_inicio")
    _safe_log("[ai_parser] prompt_final:", prompt_final)
    print("[ai_parser] prompt_final_fin")

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "Eres un parser financiero estricto y devuelves solo JSON."},
                {"role": "user", "content": prompt_final}
            ]
        )
    except Exception as e:
        print("[ai_parser] fallback_condicion: excepcion_llamada_modelo")
        print("[ai_parser] error_llamada_modelo:", repr(e))
        traceback.print_exc()
        raise

    contenido = response.choices[0].message.content or "{}"
    _safe_log("[ai_parser] respuesta_cruda_modelo:", contenido)

    try:
        parsed = json.loads(contenido)
    except json.JSONDecodeError:
        print("[ai_parser] fallback_condicion: json_decode_error")
        return {
            "intent": "mensaje_ambiguo",
            "should_save": False,
            "needs_clarification": True,
            "clarification_message": "No pude interpretar el movimiento. Indica tipo y monto, por ejemplo: 'gasto 12000 en comida'.",
            "tipo": None,
            "descripcion": "",
            "monto": None,
            "periodo": "",
            "query_scope": "",
            "categoria_consulta": "",
            "categoria": "otros",
            "fecha": None,
            "categoria_nueva_nombre": "",
            "categoria_nueva_descripcion": "",
        }

    parsed_normalizado = {
        "intent": parsed.get("intent", "mensaje_ambiguo"),
        "should_save": bool(parsed.get("should_save", False)),
        "needs_clarification": bool(parsed.get("needs_clarification", False)),
        "clarification_message": parsed.get("clarification_message") or "",
        "tipo": parsed.get("tipo"),
        "descripcion": (parsed.get("descripcion") or "").strip(),
        "monto": parsed.get("monto"),
        "periodo": (parsed.get("periodo") or "").strip(),
        "query_scope": (parsed.get("query_scope") or "").strip(),
        "categoria_consulta": (parsed.get("categoria_consulta") or "").strip(),
        "categoria": (parsed.get("categoria") or "otros").strip(),
        "fecha": parsed.get("fecha"),
        "categoria_nueva_nombre": (parsed.get("categoria_nueva_nombre") or "").strip(),
        "categoria_nueva_descripcion": (parsed.get("categoria_nueva_descripcion") or "").strip(),
    }
    _safe_log("[ai_parser] json_parseado:", parsed_normalizado)
    return parsed_normalizado
