from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Pedido, Cliente, Proveedor
from ..auth import get_current_user, verificar_rol, oauth2_scheme
from ..templates import templates
from datetime import datetime

router = APIRouter()

# ---- Rutas para administradores y operativos ----
@router.get("/", response_class=HTMLResponse)
async def listar_pedidos(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = await get_current_user(token)
    verificar_rol(user, ["admin", "operativo", "auditor"])
    pedidos = db.query(Pedido).order_by(Pedido.fecha.desc()).all()
    clientes = db.query(Cliente).all()
    proveedores = db.query(Proveedor).all()
    return templates.TemplateResponse("admin_pedidos.html", {
        "request": request,
        "user": user,
        "pedidos": pedidos,
        "clientes": clientes,
        "proveedores": proveedores
    })

@router.post("/crear")
async def crear_pedido_admin(
    request: Request,
    cliente_id: int = Form(...),
    tamano: str = Form(...),
    cantidad: int = Form(...),
    precio_unitario: float = Form(0.0),
    exonerado: bool = Form(False),
    proveedor_id: int = Form(None),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = await get_current_user(token)
    verificar_rol(user, ["admin", "operativo"])

    if cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a cero")

    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    pedido = Pedido(
        cliente_id=cliente_id,
        tamano=tamano,
        cantidad=cantidad,
        precio_unitario=0 if exonerado else precio_unitario,
        exonerado=exonerado,
        proveedor_id=proveedor_id,
        estado="pendiente"
    )
    db.add(pedido)
    db.commit()
    return RedirectResponse(url="/pedidos/", status_code=303)

@router.post("/actualizar_estado")
async def actualizar_estado(
    pedido_id: int = Form(...),
    nuevo_estado: str = Form(...),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = await get_current_user(token)
    verificar_rol(user, ["admin", "operativo"])

    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    pedido.estado = nuevo_estado
    db.commit()
    return RedirectResponse(url="/pedidos/", status_code=303)

# ---- Rutas para clientes ----
@router.get("/cliente/dashboard", response_class=HTMLResponse)
async def cliente_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = await get_current_user(token)
    verificar_rol(user, ["cliente"])

    cliente = db.query(Cliente).filter(Cliente.cedula_rif == user.username).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Perfil de cliente no configurado")

    pedidos = db.query(Pedido).filter(Pedido.cliente_id == cliente.id).order_by(Pedido.fecha.desc()).all()
    return templates.TemplateResponse("cliente_dashboard.html", {
        "request": request,
        "user": user,
        "cliente": cliente,
        "pedidos": pedidos
    })

@router.post("/cliente/crear_pedido")
async def cliente_crear_pedido(
    request: Request,
    tamano: str = Form(...),
    cantidad: int = Form(...),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = await get_current_user(token)
    verificar_rol(user, ["cliente"])

    if cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a cero")

    cliente = db.query(Cliente).filter(Cliente.cedula_rif == user.username).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    pedido = Pedido(
        cliente_id=cliente.id,
        tamano=tamano,
        cantidad=cantidad,
        precio_unitario=0.0,
        exonerado=cliente.tipo == "Institución Exonerada",
        estado="pendiente"
    )
    db.add(pedido)
    db.commit()
    return RedirectResponse(url="/pedidos/cliente/dashboard", status_code=303)
