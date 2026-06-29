import math
from sqlalchemy.orm import Session
from .models import Pedido, DetallePedido

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def calcular_utilidad(pedido_id: int, db: Session):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        return {"error": "Pedido no encontrado"}
    
    detalles = db.query(DetallePedido).filter(DetallePedido.pedido_id == pedido_id).all()
    ingreso_total = sum(float(d.precio_unitario) * d.cantidad for d in detalles if not d.exonerado)
    utilidad_bruta = ingreso_total - float(pedido.costo_logistico)
    utilidad_neta = utilidad_bruta - float(pedido.costo_administrativo)
    
    return {
        "ingreso_total": ingreso_total,
        "costo_logistico": float(pedido.costo_logistico),
        "costo_administrativo": float(pedido.costo_administrativo),
        "utilidad_bruta": utilidad_bruta,
        "utilidad_neta": utilidad_neta
    }
