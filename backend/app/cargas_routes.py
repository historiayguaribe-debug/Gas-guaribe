from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Carga, Proveedor, Cilindro
from .auth import get_current_user, get_db, oauth2_scheme, verificar_rol
from .utils import generar_codigo_qr
from .templates import templates
from datetime import datetime

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def listar_cargas(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    verificar_rol(user, ["admin", "operativo", "auditor"])
    cargas = db.query(Carga).order_by(Carga.fecha.desc()).all()
    proveedores = db.query(Proveedor).all()
    return templates.TemplateResponse("admin_cargas.html", {"request": request, "user": user, "cargas": cargas, "proveedores": proveedores})

@router.post("/crear")
async def crear_carga(
    request: Request,
    proveedor_id: int = Form(...),
    cantidad_P: int = Form(0),
    cantidad_M: int = Form(0),
    cantidad_G: int = Form(0),
    numero_factura: str = Form(...),
    gastos_logisticos: float = Form(0.0),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user = await get_current_user(token)
    verificar_rol(user, ["admin", "operativo"])
    if cantidad_P < 0 or cantidad_M < 0 or cantidad_G < 0:
        raise HTTPException(status_code=400, detail="Las cantidades no pueden ser negativas")
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    costo_total = (cantidad_P * proveedor.precio_P +
                   cantidad_M * proveedor.precio_M +
                   cantidad_G * proveedor.precio_G)
    carga = Carga(
        proveedor_id=proveedor_id,
        cantidad_P=cantidad_P,
        cantidad_M=cantidad_M,
        cantidad_G=cantidad_G,
        costo_total=costo_total,
        numero_factura=numero_factura,
        gastos_logisticos=gastos_logisticos,
        fecha=datetime.utcnow()
    )
    db.add(carga)
    db.commit()
    # Crear cilindros
    for tam, cant in [("P", cantidad_P), ("M", cantidad_M), ("G", cantidad_G)]:
        for _ in range(cant):
            precio_venta = getattr(proveedor, f"precio_{tam}") * 1.3
            cil = Cilindro(
                codigo_qr=generar_codigo_qr(),
                tamano=tam,
                estado="disponible",
                proveedor_id=proveedor_id,
                costo_compra=getattr(proveedor, f"precio_{tam}"),
                precio_venta=precio_venta
            )
            db.add(cil)
    db.commit()
    return RedirectResponse(url="/cargas/", status_code=303)
