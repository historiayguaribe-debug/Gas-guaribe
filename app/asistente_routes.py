from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Venta, Carga, GastoOperativo, Cliente, Cilindro, Pedido
from ..auth import get_current_user, verificar_rol, oauth2_scheme
from ..templates import templates
from ..config import settings
from groq import Groq
import json

client = Groq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def chat_page(
    request: Request,
    token: str = Depends(oauth2_scheme)
):
    user = await get_current_user(token)
    # Solo admin y operativo pueden usar el asistente (opcional)
    verificar_rol(user, ["admin", "operativo"])
    return templates.TemplateResponse("admin_chat.html", {"request": request, "user": user})

@router.post("/consultar")
async def consultar_ia(
    request: Request,
    pregunta: str = Form(...),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = await get_current_user(token)
    verificar_rol(user, ["admin", "operativo"])

    if not client:
        return JSONResponse({
            "respuesta": "El asistente IA no está configurado (falta GROQ_API_KEY)."
        })

    # Obtener datos resumidos
    total_clientes = db.query(func.count(Cliente.id)).scalar() or 0
    cilindros_disp = db.query(func.count(Cilindro.id)).filter(Cilindro.estado == "disponible").scalar() or 0
    pedidos_pend = db.query(func.count(Pedido.id)).filter(Pedido.estado == "pendiente").scalar() or 0
    ingresos = db.query(func.sum(Venta.cantidad * Venta.precio_unitario)).scalar() or 0.0
    costos = db.query(func.sum(Carga.costo_total)).scalar() or 0.0
    gastos = db.query(func.sum(GastoOperativo.monto)).scalar() or 0.0
    utilidad = ingresos - costos - gastos
    exoneraciones = db.query(func.count(Venta.id)).filter(Venta.exonerado == True).scalar() or 0

    contexto = f"""
    Datos de GAS GUARIBE:
    - Clientes: {total_clientes}
    - Cilindros disponibles: {cilindros_disp}
    - Pedidos pendientes: {pedidos_pend}
    - Ingresos: {ingresos:.2f} Bs.
    - Costos: {costos + gastos:.2f} Bs.
    - Utilidad: {utilidad:.2f} Bs.
    - Exoneraciones: {exoneraciones}
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Eres un asistente de GAS GUARIBE. Responde preguntas basadas en los datos proporcionados."},
                {"role": "user", "content": f"{contexto}\nPregunta: {pregunta}"}
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        respuesta = completion.choices[0].message.content
        return JSONResponse({"respuesta": respuesta})
    except Exception as e:
        return JSONResponse({"respuesta": f"Error al consultar IA: {str(e)}"}, status_code=500)
