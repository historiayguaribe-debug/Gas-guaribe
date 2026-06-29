from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import get_db
from .models import Pedido, DetallePedido, Cilindro
from .auth import get_current_user
from .calculos import haversine
import datetime

router = APIRouter(prefix="/reportes", tags=["Reportes"])

@router.get("/resumen-diario")
def resumen_diario(db: Session = Depends(get_db), user=Depends(get_current_user)):
    hoy = datetime.datetime.utcnow().date()
    pedidos_hoy = db.query(Pedido).filter(Pedido.fecha_creacion >= hoy).all()
    
    total_pedidos = len(pedidos_hoy)
    total_ingresos = sum(float(p.monto_total) for p in pedidos_hoy if p.estado == "entregado")
    total_exonerados = 0
    for p in pedidos_hoy:
        detalles = db.query(DetallePedido).filter(DetallePedido.pedido_id == p.id).all()
        for d in detalles:
            if d.exonerado:
                total_exonerados += d.cantidad

    return {
        "fecha": str(hoy),
        "total_pedidos": total_pedidos,
        "ingresos_del_dia": round(total_ingresos, 2),
        "cilindros_exonerados_hoy": total_exonerados
    }

@router.get("/utilidad-acumulada")
def utilidad_acumulada(db: Session = Depends(get_db), user=Depends(get_current_user)):
    pedidos = db.query(Pedido).filter(Pedido.estado == "entregado").all()
    ingreso_total = 0
    costo_logistico_total = 0
    costo_admin_total = 0
    for p in pedidos:
        ingreso_total += float(p.monto_total)
        costo_logistico_total += float(p.costo_logistico)
        costo_admin_total += float(p.costo_administrativo)
    
    utilidad_bruta = ingreso_total - costo_logistico_total
    utilidad_neta = utilidad_bruta - costo_admin_total
    
    return {
        "ingresos_totales": round(ingreso_total, 2),
        "costos_logisticos": round(costo_logistico_total, 2),
        "costos_administrativos": round(costo_admin_total, 2),
        "utilidad_bruta": round(utilidad_bruta, 2),
        "utilidad_neta": round(utilidad_neta, 2)
    }
