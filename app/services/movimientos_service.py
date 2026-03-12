from app.database.supabase_client import supabase
from datetime import date

def guardar_movimiento(movimiento):

    fecha = movimiento["fecha"]

    if fecha == "hoy":
        fecha = date.today().isoformat()

    data = {
        "tipo": movimiento["tipo"],
        "descripcion": movimiento["descripcion"],
        "monto": movimiento["monto"],
        "categoria": movimiento["categoria"],
        "fecha": fecha
    }

    response = supabase.table("movimientos").insert(data).execute()

    return response