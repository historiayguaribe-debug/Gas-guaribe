from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import SessionLocal
from .models import Venta, Carga, GastoOperativo, Cliente, Cilindro, Pedido, Proveedor, Comunidad
from .auth import get_current_user, get_db, oauth2_scheme, verificar_rol
from .templates import templates
from .config import GROQ_API_KEY
from groq import Groq
import json
from datetime import datetime

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

router = APIRouter()

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
async def chat_page(request: Request, token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    return templates.TemplateResponse("admin_chat.html", {"request": request, "user": user})

@router.post("/consultar")
async def consultar_ia(request: Request, pregunta: str = Form(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    es_admin = user.role == "admin"
    
    # Contexto resumido
    total_clientes = db.query(func.count(Cliente.id)).scalar()
    cilindros_disp = db.query(func.count(Cilindro.id)).filter(Cilindro.estado == "disponible").scalar()
    pedidos_pend = db.query(func.count(Pedido.id)).filter(Pedido.estado == "pendiente").scalar()
    ingresos = db.query(func.sum(Venta.cantidad * Venta.precio_unitario)).scalar() or 0.0
    costos = db.query(func.sum(Carga.costo_total)).scalar() or 0.0
    gastos = db.query(func.sum(GastoOperativo.monto)).scalar() or 0.0
    utilidad = ingresos - costos - gastos
    exoneraciones = db.query(func.count(Venta.id)).filter(Venta.exonerado == True).scalar()

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

    if es_admin and client:
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Eres un asistente administrativo de GAS GUARIBE. Puedes ejecutar acciones si el usuario lo solicita."},
                    {"role": "user", "content": f"{contexto}\nPregunta: {pregunta}"}
                ],
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1024,
            )
            response_message = completion.choices[0].message
            tool_calls = response_message.tool_calls
            if tool_calls:
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    try:
                        resultado = ejecutar_funcion(db, function_name, arguments)
                        db.commit()
                        return JSONResponse({"respuesta": f"Acción ejecutada: {function_name}. Resultado: {resultado}"})
                    except Exception as e:
                        db.rollback()
                        return JSONResponse({"respuesta": f"Error al ejecutar {function_name}: {str(e)}"}, status_code=500)
            else:
                return JSONResponse({"respuesta": response_message.content})
        except Exception as e:
            return JSONResponse({"respuesta": f"Error en IA: {str(e)}"}, status_code=500)
    else:
        # Solo consulta
        if not client:
            return JSONResponse({"respuesta": "El asistente IA no está configurado (falta GROQ_API_KEY)."})
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Eres un asistente de GAS GUARIBE. Solo responde preguntas basadas en los datos, no ejecutes acciones."},
                    {"role": "user", "content": f"{contexto}\nPregunta: {pregunta}"}
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            return JSONResponse({"respuesta": completion.choices[0].message.content})
        except Exception as e:
            return JSONResponse({"respuesta": f"Error: {str(e)}"}, status_code=500)

def ejecutar_funcion(db, func_name, args):
    if func_name == "crear_cliente":
        comunidad = db.query(Comunidad).filter(Comunidad.id == args["comunidad_id"]).first()
        if not comunidad:
            return "Error: Comunidad no encontrada"
        cliente = Cliente(
            nombre=args["nombre"],
            cedula_rif=args["cedula_rif"],
            telefono=args["telefono"],
            direccion=args["direccion"],
            comunidad_id=args["comunidad_id"],
            tipo=args.get("tipo", "Normal")
        )
        db.add(cliente)
        db.flush()
        return f"Cliente {cliente.nombre} creado con ID {cliente.id}"
    
    elif func_name == "registrar_venta":
        cliente = db.query(Cliente).filter(Cliente.id == args["cliente_id"]).first()
        if not cliente:
            return "Error: Cliente no encontrado"
        proveedor = db.query(Proveedor).filter(Proveedor.id == args["proveedor_id"]).first()
        if not proveedor:
            return "Error: Proveedor no encontrado"
        disponibles = db.query(Cilindro).filter(Cilindro.tamano == args["tamano"], Cilindro.estado == "disponible").count()
        if disponibles < args["cantidad"]:
            return f"No hay suficientes cilindros tamaño {args['tamano']}. Disponibles: {disponibles}"
        venta = Venta(
            cliente_id=args["cliente_id"],
            proveedor_id=args["proveedor_id"],
            tamano=args["tamano"],
            cantidad=args["cantidad"],
            precio_unitario=args.get("precio_unitario", 0.0),
            exonerado=args.get("exonerado", False)
        )
        db.add(venta)
        db.flush()
        cilindros = db.query(Cilindro).filter(Cilindro.tamano == args["tamano"], Cilindro.estado == "disponible").limit(args["cantidad"]).all()
        for c in cilindros:
            c.estado = "en_ruta"
        return f"Venta registrada: {args['cantidad']} cilindros {args['tamano']} a {cliente.nombre}"
    
    elif func_name == "registrar_carga":
        proveedor = db.query(Proveedor).filter(Proveedor.id == args["proveedor_id"]).first()
        if not proveedor:
            return "Error: Proveedor no encontrado"
        cant_P = args.get("cantidad_P", 0)
        cant_M = args.get("cantidad_M", 0)
        cant_G = args.get("cantidad_G", 0)
        costo_total = cant_P * proveedor.precio_P + cant_M * proveedor.precio_M + cant_G * proveedor.precio_G
        carga = Carga(
            proveedor_id=args["proveedor_id"],
            cantidad_P=cant_P,
            cantidad_M=cant_M,
            cantidad_G=cant_G,
            costo_total=costo_total,
            numero_factura=args["numero_factura"],
            gastos_logisticos=args.get("gastos_logisticos", 0.0)
        )
        db.add(carga)
        db.flush()
        from .utils import generar_codigo_qr
        for tam, cant in [("P", cant_P), ("M", cant_M), ("G", cant_G)]:
            for _ in range(cant):
                precio_venta = getattr(proveedor, f"precio_{tam}") * 1.3
                cil = Cilindro(
                    codigo_qr=generar_codigo_qr(),
                    tamano=tam,
                    estado="disponible",
                    proveedor_id=proveedor.id,
                    costo_compra=getattr(proveedor, f"precio_{tam}"),
                    precio_venta=precio_venta
                )
                db.add(cil)
        return f"Carga registrada. Factura {args['numero_factura']}. Total: {costo_total:.2f}"
    
    elif func_name == "crear_pedido":
        cliente = db.query(Cliente).filter(Cliente.id == args["cliente_id"]).first()
        if not cliente:
            return "Error: Cliente no encontrado"
        pedido = Pedido(
            cliente_id=args["cliente_id"],
            tamano=args["tamano"],
            cantidad=args["cantidad"],
            exonerado=args.get("exonerado", False),
            estado="pendiente"
        )
        db.add(pedido)
        db.flush()
        return f"Pedido creado para {cliente.nombre}: {args['cantidad']} cilindros {args['tamano']}"
    
    elif func_name == "actualizar_estado_pedido":
        pedido = db.query(Pedido).filter(Pedido.id == args["pedido_id"]).first()
        if not pedido:
            return "Error: Pedido no encontrado"
        pedido.estado = args["nuevo_estado"]
        return f"Estado del pedido {pedido.id} actualizado a {args['nuevo_estado']}"
    
    else:
        return "Función no implementada"
