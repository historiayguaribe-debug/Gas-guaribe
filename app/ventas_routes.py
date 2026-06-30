from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Venta, Cliente, Proveedor, Cilindro
from .auth import get_current_user, get_db, oauth2_scheme, verificar_rol
from .templates import templates
from datetime import datetime

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def listar_ventas(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    verificar_rol(user, ["admin", "operativo", "auditor"])
    ventas = db.query(Venta).order_by(Venta.fecha.desc()).all()
    clientes = db.query(Cliente).all()
    proveedores = db.query(Proveedor).all()
    return templates.TemplateResponse("admin_ventas.html", {"request": request, "user": user, "ventas": ventas, "clientes": clientes, "proveedores": proveedores})

@router.post("/crear")
async def crear_venta(
    request: Request,
    cliente_id: int = Form(...),
    proveedor_id: int = Form(...),
    tamano: str = Form(...),
    cantidad: int = Form(...),
    precio_unitario: float = Form(...),
    exonerado: bool = Form(False),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = await get_current_user(token)
    verificar_rol(user, ["admin", "operativo"])
    if cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a cero")
    disponibles = db.query(Cilindro).filter(Cilindro.tamano == tamano, Cilindro.estado == "disponible").count()
    if disponibles < cantidad:
        raise HTTPException(status_code=400, detail=f"No hay suficientes cilindros tamaño {tamano}. Disponibles: {disponibles}")
    venta = Venta(
        cliente_id=cliente_id,
        proveedor_id=proveedor_id,
        tamano=tamano,
        cantidad=cantidad,
        precio_unitario=precio_unitario if not exonerado else 0,
        exonerado=exonerado,
        fecha=datetime.utcnow()
    )
    db.add(venta)
    db.commit()
    cilindros = db.query(Cilindro).filter(Cilindro.tamano == tamano, Cilindro.estado == "disponible").limit(cantidad).all()
    for cil in cilindros:
        cil.estado = "en_ruta"
    db.commit()
    return RedirectResponse(url="/ventas/", status_code=303)
