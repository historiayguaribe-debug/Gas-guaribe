from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from .database import get_db
from .models import Planta, Cilindro, Pedido, DetallePedido, Cliente, CostoOperativo, Usuario
from .auth import get_current_user, hash_password
import random
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/admin", tags=["Administración"])
templates = Jinja2Templates(directory="templates")

# --- MODELOS PARA PETICIONES JSON ---
class CargaRequest(BaseModel):
    planta_id: int
    fecha: str
    cantidades: dict  # {"P": 10, "M": 5, "G": 3}
    costo_total: float
    factura: str
    gastos_logisticos: float = 0.0

class VentaRequest(BaseModel):
    cliente_id: int
    planta_id: int
    tamanio: str  # "P", "M", "G"
    cantidad: int
    fecha: str
    precio_unitario: float

class ClienteRequest(BaseModel):
    nombre: str
    email: str
    telefono: str
    direccion: str
    exonerado: bool = False

# --- RUTAS HTML (VISTAS) ---
@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

@router.get("/cargas", response_class=HTMLResponse)
async def admin_cargas(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    plantas = db.query(Planta).all()
    return templates.TemplateResponse("admin_cargas.html", {"request": request, "plantas": plantas})

@router.get("/ventas", response_class=HTMLResponse)
async def admin_ventas(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    clientes = db.query(Cliente).all()
    plantas = db.query(Planta).all()
    return templates.TemplateResponse("admin_ventas.html", {"request": request, "clientes": clientes, "plantas": plantas})

@router.get("/clientes", response_class=HTMLResponse)
async def admin_clientes(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    clientes = db.query(Cliente).all()
    return templates.TemplateResponse("admin_clientes.html", {"request": request, "clientes": clientes})

@router.get("/reportes", response_class=HTMLResponse)
async def admin_reportes(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("admin_reportes.html", {"request": request})

@router.get("/asistente", response_class=HTMLResponse)
async def admin_asistente(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("admin_chat.html", {"request": request})

# --- ENDPOINTS DE DATOS (API) ---

@router.get("/estadisticas")
async def get_estadisticas(db: Session = Depends(get_db), user=Depends(get_current_user)):
    hoy = date.today()
    inicio_mes = hoy.replace(day=1)

    total_cilindros = db.query(Cilindro).count()
    pedidos_hoy = db.query(Pedido).filter(Pedido.fecha_creacion >= hoy).count()
    ingresos_hoy = sum(
        float(p.monto_total) for p in db.query(Pedido).filter(
            Pedido.fecha_creacion >= hoy, Pedido.estado == "entregado"
        ).all()
    )
    exonerados_hoy = db.query(DetallePedido).filter(
        DetallePedido.exonerado == True,
        DetallePedido.pedido.has(Pedido.fecha_creacion >= hoy)
    ).count()

    # Ventas por tamaño (últimos 30 días)
    ventas_tamano = {"P": 0, "M": 0, "G": 0}
    detalles = db.query(DetallePedido).join(Pedido).filter(Pedido.fecha_creacion >= (hoy - timedelta(days=30))).all()
    for d in detalles:
        if d.cilindro:
            tam = d.cilindro.tamanio.value if hasattr(d.cilindro.tamanio, 'value') else str(d.cilindro.tamanio)
            ventas_tamano[tam] = ventas_tamano.get(tam, 0) + d.cantidad

    # Utilidad acumulada
    pedidos_entregados = db.query(Pedido).filter(Pedido.estado == "entregado").all()
    ingreso_total = sum(float(p.monto_total) for p in pedidos_entregados)
    costo_logistico = sum(float(p.costo_logistico) for p in pedidos_entregados)
    costo_admin = sum(float(p.costo_administrativo) for p in pedidos_entregados)
    utilidad_bruta = ingreso_total - costo_logistico
    utilidad_neta = utilidad_bruta - costo_admin

    pedidos_recientes = db.query(Pedido).order_by(Pedido.fecha_creacion.desc()).limit(5).all()
    pedidos_data = []
    for p in pedidos_recientes:
        cliente = db.query(Cliente).filter(Cliente.id == p.cliente_id).first()
        pedidos_data.append({
            "id": p.id,
            "cliente": cliente.usuario.nombre if cliente and cliente.usuario else f"Cliente {p.cliente_id}",
            "total": float(p.monto_total),
            "estado": p.estado,
            "fecha": p.fecha_creacion.strftime("%Y-%m-%d")
        })

    return {
        "total_cilindros": total_cilindros,
        "pedidos_hoy": pedidos_hoy,
        "ingresos_hoy": round(ingresos_hoy, 2),
        "exonerados_hoy": exonerados_hoy,
        "ventas_por_tamano": ventas_tamano,
        "utilidad": {
            "ingreso_total": round(ingreso_total, 2),
            "costo_logistico": round(costo_logistico, 2),
            "costo_administrativo": round(costo_admin, 2),
            "utilidad_bruta": round(utilidad_bruta, 2),
            "utilidad_neta": round(utilidad_neta, 2),
        },
        "pedidos_recientes": pedidos_data
    }

@router.post("/cargas")
async def registrar_carga(data: CargaRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    planta = db.query(Planta).filter(Planta.id == data.planta_id).first()
    if not planta:
        raise HTTPException(status_code=404, detail="Planta no encontrada")

    fecha_dt = datetime.strptime(data.fecha, "%Y-%m-%d")
    total_cilindros = sum(data.cantidades.values())

    if total_cilindros == 0:
        raise HTTPException(status_code=400, detail="Debe ingresar al menos un cilindro")

    costo_promedio = data.costo_total / total_cilindros

    for tam, cantidad in data.cantidades.items():
        if cantidad <= 0:
            continue
        for _ in range(cantidad):
            codigo = f"{planta.nombre[:3].upper()}-{tam}-{fecha_dt.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            cilindro = Cilindro(
                codigo_qr=codigo,
                tamanio=tam,
                estado="disponible",
                planta_id=data.planta_id,
                costo_compra=costo_promedio,
                precio_venta=costo_promedio * 1.3
            )
            db.add(cilindro)

    if data.gastos_logisticos > 0:
        costo = CostoOperativo(
            tipo="Logístico",
            descripcion=f"Gastos logísticos carga {data.factura}",
            monto=data.gastos_logisticos,
            fecha=fecha_dt
        )
        db.add(costo)

    db.commit()
    return {"mensaje": "Carga registrada exitosamente", "total_cilindros": total_cilindros}

@router.post("/ventas")
async def registrar_venta(data: VentaRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    cliente = db.query(Cliente).filter(Cliente.id == data.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    planta = db.query(Planta).filter(Planta.id == data.planta_id).first()
    if not planta:
        raise HTTPException(status_code=404, detail="Planta no encontrada")

    cilindros = db.query(Cilindro).filter(
        Cilindro.planta_id == data.planta_id,
        Cilindro.tamanio == data.tamanio,
        Cilindro.estado == "disponible"
    ).limit(data.cantidad).all()

    if len(cilindros) < data.cantidad:
        raise HTTPException(status_code=400, detail=f"No hay suficientes cilindros de tamaño {data.tamanio}. Disponibles: {len(cilindros)}")

    fecha_dt = datetime.strptime(data.fecha, "%Y-%m-%d")

    pedido = Pedido(
        cliente_id=data.cliente_id,
        planta_asignada_id=data.planta_id,
        direccion_entrega=cliente.direccion,
        lat_entrega=cliente.lat,
        lng_entrega=cliente.lng,
        estado="entregado",
        costo_logistico=0.0,
        costo_administrativo=0.0,
        monto_total=0,
        fecha_creacion=fecha_dt,
        fecha_entrega=fecha_dt
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)

    total_pedido = 0
    for cil in cilindros:
        precio = data.precio_unitario if not cliente.exonerado else 0
        total_pedido += precio
        detalle = DetallePedido(
            pedido_id=pedido.id,
            cilindro_id=cil.id,
            cantidad=1,
            precio_unitario=precio,
            exonerado=cliente.exonerado
        )
        db.add(detalle)
        cil.estado = "vacio"

    pedido.monto_total = total_pedido
    db.commit()
    return {"mensaje": "Venta registrada exitosamente", "pedido_id": pedido.id, "total": total_pedido}

@router.post("/clientes")
async def registrar_cliente(data: ClienteRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    from .models import Usuario
    existe = db.query(Usuario).filter(Usuario.email == data.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    nuevo_usuario = Usuario(
        email=data.email,
        hashed_password=hash_password("1234"),
        nombre=data.nombre,
        telefono=data.telefono,
        rol="cliente"
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    nuevo_cliente = Cliente(
        usuario_id=nuevo_usuario.id,
        direccion=data.direccion,
        lat=10.0,
        lng=-66.0,
        es_institucion=data.exonerado,
        exonerado=data.exonerado
    )
    db.add(nuevo_cliente)
    db.commit()
    return {"mensaje": "Cliente registrado exitosamente", "cliente_id": nuevo_cliente.id}

# --- RUTAS DE COMPATIBILIDAD ---
@router.get("/panel", response_class=HTMLResponse)
async def panel_administracion(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("admin_panel.html", {"request": request})

@router.get("/carga-planta", response_class=HTMLResponse)
async def formulario_carga_planta(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    plantas = db.query(Planta).all()
    return templates.TemplateResponse("carga_planta.html", {"request": request, "plantas": plantas})

@router.get("/venta", response_class=HTMLResponse)
async def formulario_venta(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    clientes = db.query(Cliente).all()
    plantas = db.query(Planta).all()
    return templates.TemplateResponse("venta_cilindro.html", {"request": request, "clientes": clientes, "plantas": plantas})

@router.get("/costo", response_class=HTMLResponse)
async def formulario_costo(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("costo_operativo.html", {"request": request})
    
