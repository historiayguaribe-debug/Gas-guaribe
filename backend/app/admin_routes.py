from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from .database import get_db
from .models import Planta, Cilindro, Pedido, DetallePedido, Cliente, CostoOperativo
from .auth import get_current_user
import random

router = APIRouter(prefix="/admin", tags=["Administración"])
templates = Jinja2Templates(directory="templates")

# --- PÁGINA PRINCIPAL DEL PANEL ---
@router.get("/panel", response_class=HTMLResponse)
async def panel_administracion(request: Request, user=Depends(get_current_user)):
    """Panel principal con enlaces a todas las opciones."""
    return templates.TemplateResponse("admin_panel.html", {"request": request})

# --- FORMULARIO PARA REGISTRAR CARGA A PLANTA ---
@router.get("/carga-planta", response_class=HTMLResponse)
async def formulario_carga_planta(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Muestra el formulario para registrar una carga de cilindros a una planta."""
    plantas = db.query(Planta).all()
    return templates.TemplateResponse("carga_planta.html", {"request": request, "plantas": plantas})

@router.post("/carga-planta")
async def registrar_carga_planta(
    request: Request,
    planta_id: int = Form(...),
    tamanio: str = Form(...),
    cantidad: int = Form(...),
    costo_unitario: float = Form(...),
    precio_venta: float = Form(...),
    fecha: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """Guarda una carga de cilindros en la base de datos."""
    planta = db.query(Planta).filter(Planta.id == planta_id).first()
    if not planta:
        raise HTTPException(status_code=404, detail="Planta no encontrada")
    
    fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
    for i in range(cantidad):
        codigo = f"{planta.nombre[:3].upper()}-{tamanio}-{fecha_dt.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        cilindro = Cilindro(
            codigo_qr=codigo,
            tamanio=tamanio,
            estado="disponible",
            planta_id=planta_id,
            costo_compra=costo_unitario,
            precio_venta=precio_venta
        )
        db.add(cilindro)
    
    db.commit()
    return RedirectResponse(url="/admin/panel", status_code=303)

# --- FORMULARIO PARA REGISTRAR VENTA ---
@router.get("/venta", response_class=HTMLResponse)
async def formulario_venta(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Muestra el formulario para registrar una venta de cilindros."""
    clientes = db.query(Cliente).all()
    plantas = db.query(Planta).all()
    return templates.TemplateResponse("venta_cilindro.html", {"request": request, "clientes": clientes, "plantas": plantas})

@router.post("/venta")
async def registrar_venta(
    request: Request,
    cliente_id: int = Form(...),
    planta_id: int = Form(...),
    tamanio: str = Form(...),
    cantidad: int = Form(...),
    fecha: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """Guarda una venta de cilindros en la base de datos."""
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    planta = db.query(Planta).filter(Planta.id == planta_id).first()
    if not planta:
        raise HTTPException(status_code=404, detail="Planta no encontrada")
    
    cilindros = db.query(Cilindro).filter(
        Cilindro.planta_id == planta_id,
        Cilindro.tamanio == tamanio,
        Cilindro.estado == "disponible"
    ).limit(cantidad).all()
    
    if len(cilindros) < cantidad:
        raise HTTPException(status_code=400, detail=f"No hay suficientes cilindros de tamaño {tamanio}. Disponibles: {len(cilindros)}")
    
    fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
    pedido = Pedido(
        cliente_id=cliente_id,
        planta_asignada_id=planta_id,
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
        precio = cil.precio_venta if not cliente.exonerado else 0
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
    return RedirectResponse(url="/admin/panel", status_code=303)

# --- FORMULARIO PARA REGISTRAR COSTO OPERATIVO ---
@router.get("/costo", response_class=HTMLResponse)
async def formulario_costo(request: Request, user=Depends(get_current_user)):
    """Muestra el formulario para registrar un costo operativo."""
    return templates.TemplateResponse("costo_operativo.html", {"request": request})

@router.post("/costo")
async def registrar_costo(
    request: Request,
    tipo: str = Form(...),
    descripcion: str = Form(...),
    monto: float = Form(...),
    fecha: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """Guarda un costo operativo en la base de datos."""
    fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
    costo = CostoOperativo(
        tipo=tipo,
        descripcion=descripcion,
        monto=monto,
        fecha=fecha_dt
    )
    db.add(costo)
    db.commit()
    return RedirectResponse(url="/admin/panel", status_code=303)
