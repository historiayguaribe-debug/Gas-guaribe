from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import get_db
from .models import Venta, Carga, GastoOperativo, Cliente, Comunidad, Circuito
from .auth import get_current_user, verificar_rol, oauth2_scheme
from .templates import templates
import pandas as pd
from io import BytesIO

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def reportes_page(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    verificar_rol(user, ["admin", "operativo", "auditor"])
    ingresos = db.query(func.sum(Venta.cantidad * Venta.precio_unitario)).scalar() or 0.0
    costos_compras = db.query(func.sum(Carga.costo_total)).scalar() or 0.0
    gastos_total = db.query(func.sum(GastoOperativo.monto)).scalar() or 0.0
    utilidad = ingresos - costos_compras - gastos_total
    exoneraciones = db.query(func.count(Venta.id)).filter(Venta.exonerado == True).scalar() or 0

    ventas_por_circuito = db.query(Circuito.nombre, func.sum(Venta.cantidad).label('total')).join(Cliente, Venta.cliente_id == Cliente.id).join(Comunidad, Cliente.comunidad_id == Comunidad.id).join(Circuito, Comunidad.circuito_id == Circuito.id).group_by(Circuito.nombre).all()
    ventas_circuito_dict = {row.nombre: row.total for row in ventas_por_circuito}

    top_comunidades = db.query(Comunidad.nombre, func.sum(Venta.cantidad).label('total')).join(Cliente, Venta.cliente_id == Cliente.id).join(Comunidad, Cliente.comunidad_id == Comunidad.id).group_by(Comunidad.nombre).order_by(func.sum(Venta.cantidad).desc()).limit(5).all()
    top = [(row.nombre, row.total) for row in top_comunidades]

    return templates.TemplateResponse("admin_reportes.html", {"request": request, "user": user, "ingresos": ingresos, "costos_compras": costos_compras, "gastos_total": gastos_total, "utilidad": utilidad, "exoneraciones": exoneraciones, "ventas_por_circuito": ventas_circuito_dict, "top_comunidades": top})

@router.get("/exportar/excel")
async def exportar_excel(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    verificar_rol(user, ["admin", "operativo", "auditor"])
    ventas = db.query(Venta).all()
    data = []
    for v in ventas:
        data.append({"Fecha": v.fecha, "Cliente": v.cliente.nombre if v.cliente else "", "Tamaño": v.tamano, "Cantidad": v.cantidad, "Precio Unitario": v.precio_unitario, "Exonerado": v.exonerado, "Proveedor": v.proveedor.nombre if v.proveedor else ""})
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Ventas')
    output.seek(0)
    return FileResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="reporte_ventas.xlsx")
