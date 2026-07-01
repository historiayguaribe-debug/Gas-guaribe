from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import SessionLocal
from .models import Venta, Carga, GastoOperativo, Cliente, Cilindro, Pedido, Proveedor, Comunidad, Usuario
from .templates import templates
from .config import GROQ_API_KEY
from groq import Groq
import json
from datetime import datetime

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

router = APIRouter()

# Definición de funciones para tool calling (opcional, para admin)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "crear_cliente",
            "description": "Crea un nuevo cliente en el sistema",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string"},
                    "cedula_rif": {"type": "string"},
                    "telefono": {"type": "string"},
                    "direccion": {"type": "string"},
                    "comunidad_id": {"type": "integer"},
                    "tipo": {"type": "string", "enum": ["Normal", "Institución Exonerada"]}
                },
                "required": ["nombre", "cedula_rif", "telefono", "direccion", "comunidad_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_venta",
            "description": "Registra una venta (despacho) de cilindros a un cliente",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "integer"},
                    "proveedor_id": {"type": "integer"},
                    "tamano": {"type": "string", "enum": ["P", "M", "G"]},
                    "cantidad": {"type": "integer"},
                    "precio_unitario": {"type": "number"},
                    "exonerado": {"type": "boolean"}
                },
                "required": ["cliente_id", "proveedor_id", "tamano", "cantidad"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_carga",
            "description": "Registra una compra de cilindros a una planta proveedora",
            "parameters": {
                "type": "object",
                "properties": {
                    "proveedor_id": {"type": "integer"},
                    "cantidad_P": {"type": "integer"},
                    "cantidad_M": {"type": "integer"},
                    "cantidad_G": {"type": "integer"},
                    "numero_factura": {"type": "string"},
                    "gastos_logisticos": {"type": "number"}
                },
                "required": ["proveedor_id", "numero_factura"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crear_pedido",
            "description": "Crea un pedido para un cliente",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "integer"},
                    "tamano": {"type": "string", "enum": ["P", "M", "G"]},
                    "cantidad": {"type": "integer"},
                    "exonerado": {"type": "boolean"}
                },
                "required": ["cliente_id", "tamano", "cantidad"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_estado_pedido",
            "description": "Cambia el estado de un pedido",
            "parameters": {
                "type": "object",
                "properties": {
                    "pedido_id": {"type": "integer"},
                    "nuevo_estado": {"type": "string", "enum": ["pendiente", "en_ruta", "entregado", "cancelado"]}
                },
                "required": ["pedido_id", "nuevo_estado"]
            }
        }
    }
]

@router.get("/", response_class=HTMLResponse)
async def chat_page(request: Request, db: Session = Depends(SessionLocal)):
    # Usuario fijo para el menú
    user = Usuario(username="gas.guaribe", role="admin", nombre_completo="Administrador (Acceso Directo)")
    return templates.TemplateResponse("admin_chat.html", {"request": request, "user": user})

@router.post("/consultar")
async def consultar_ia(
    request: Request,
    pregunta: str = Form(...),  # <--- Campo requerido
    db: Session = Depends(SessionLocal)
):
    # Si no hay clave de Groq, responder con mensaje
    if not client:
        return JSONResponse({"respuesta": "El asistente IA no está configurado (falta GROQ_API_KEY)."})

    # Obtener contexto resumido de la base de datos
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
    - Costos (compras + gastos): {costos + gastos:.2f} Bs.
    - Utilidad: {utilidad:.2f} Bs.
    - Exoneraciones: {exoneraciones}
    """

    # Llamada a Groq (modo consulta, sin ejecutar acciones por ahora)
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
