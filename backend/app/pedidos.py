from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .models import Cliente, Planta, Repartidor, Cilindro, Pedido, DetallePedido, EstadoPedido, TamanioCilindro
from .auth import get_current_user
from .calculos import haversine
import datetime

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

@router.post("/solicitar")
def solicitar_pedido(
    cliente_id: int,
    tamanio: str,
    cantidad: int,
    direccion: str,
    lat: float,
    lng: float,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    es_exonerado = cliente.exonerado

    plantas = db.query(Planta).all()
    if not plantas:
        raise HTTPException(status_code=404, detail="No hay plantas registradas")
    
    planta_cercana = min(plantas, key=lambda p: haversine(lat, lng, p.lat, p.lng))
    
    repartidores = db.query(Repartidor).filter(Repartidor.disponible == True).all()
    repartidor_asignado = None
    for rep in repartidores:
        distancia = haversine(lat, lng, rep.lat, rep.lng)
        if distancia < 10:
            repartidor_asignado = rep
            break

    nuevo_pedido = Pedido(
        cliente_id=cliente_id,
        repartidor_id=repartidor_asignado.id if repartidor_asignado else None,
        planta_asignada_id=planta_cercana.id,
        direccion_entrega=direccion,
        lat_entrega=lat,
        lng_entrega=lng,
        estado="asignado" if repartidor_asignado else "pendiente",
        costo_logistico=0.5,
        costo_administrativo=1.0,
        monto_total=0
    )
    db.add(nuevo_pedido)
    db.commit()
    db.refresh(nuevo_pedido)

    cilindros_disponibles = db.query(Cilindro).filter(
        Cilindro.planta_id == planta_cercana.id,
        Cilindro.estado == "disponible",
        Cilindro.tamanio == tamanio
    ).limit(cantidad).all()

    if len(cilindros_disponibles) < cantidad:
        raise HTTPException(status_code=400, detail=f"No hay suficientes cilindros de tamaño {tamanio}")

    total_pedido = 0
    for cilindro in cilindros_disponibles:
        precio = 0 if es_exonerado else cilindro.precio_venta
        total_pedido += precio
        detalle = DetallePedido(
            pedido_id=nuevo_pedido.id,
            cilindro_id=cilindro.id,
            cantidad=1,
            precio_unitario=precio,
            exonerado=es_exonerado
        )
        db.add(detalle)
        cilindro.estado = "en_ruta"
    
    nuevo_pedido.monto_total = total_pedido
    db.commit()

    return {
        "pedido_id": nuevo_pedido.id,
        "estado": nuevo_pedido.estado,
        "repartidor_id": repartidor_asignado.id if repartidor_asignado else None,
        "planta": planta_cercana.nombre,
        "total": float(total_pedido),
        "exonerado": es_exonerado
    }

@router.get("/mis-pedidos/{cliente_id}")
def listar_pedidos(cliente_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    pedidos = db.query(Pedido).filter(Pedido.cliente_id == cliente_id).all()
    return pedidos

@router.put("/estado/{pedido_id}")
def actualizar_estado(pedido_id: int, nuevo_estado: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no existe")
    if nuevo_estado not in ["entregado", "cancelado"]:
        raise HTTPException(status_code=400, detail="Estado no válido")
    pedido.estado = nuevo_estado
    if nuevo_estado == "entregado":
        pedido.fecha_entrega = datetime.datetime.utcnow()
    db.commit()
    return {"mensaje": f"Pedido actualizado a {nuevo_estado}"}
