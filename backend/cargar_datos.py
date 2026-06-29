from app.database import SessionLocal
from app.models import Planta, Repartidor, Usuario, Cliente, Cilindro, TamanioCilindro, Pedido, DetallePedido, CostoOperativo
from app.auth import hash_password
from datetime import datetime, timedelta
import random

def cargar_datos():
    db = SessionLocal()
    
    # Verificar si ya hay datos
    if db.query(Usuario).count() > 0:
        print("⚠️  Ya existen datos. No se cargarán duplicados.")
        db.close()
        return

    print("🔄 Cargando datos de prueba...")

    # 1. Plantas
    plantas = [
        Planta(nombre="Altagracia de Orituco", lat=9.8667, lng=-66.3833, capacidad_diaria=200, direccion="Calle Principal, Altagracia"),
        Planta(nombre="Valle de la Pascua", lat=9.2000, lng=-66.0000, capacidad_diaria=150, direccion="Av. Bolívar, Valle de la Pascua"),
        Planta(nombre="Puerto La Cruz", lat=10.2167, lng=-64.6167, capacidad_diaria=300, direccion="Zona Industrial, Puerto La Cruz")
    ]
    for p in plantas:
        db.add(p)
    db.commit()
    print("✅ 3 Plantas agregadas.")

    # 2. Usuarios y repartidores
    usuarios = [
        {"email": "repartidor1@test.com", "password": "1234", "nombre": "Juan Perez", "telefono": "0412-1234567", "rol": "repartidor"},
        {"email": "repartidor2@test.com", "password": "1234", "nombre": "Maria Lopez", "telefono": "0412-2345678", "rol": "repartidor"},
        {"email": "cliente@test.com", "password": "1234", "nombre": "Carlos Gomez", "telefono": "0412-9876543", "rol": "cliente"},
        {"email": "escuela@test.com", "password": "1234", "nombre": "Escuela Bolivariana", "telefono": "0412-1111111", "rol": "cliente"},
        {"email": "admin@test.com", "password": "1234", "nombre": "Admin Guaribe", "telefono": "0412-0000000", "rol": "admin"},
    ]
    for u in usuarios:
        user = Usuario(email=u["email"], hashed_password=hash_password(u["password"]), nombre=u["nombre"], telefono=u["telefono"], rol=u["rol"])
        db.add(user)
    db.commit()

    # 3. Repartidores
    rep1 = Repartidor(usuario_id=1, vehiculo="Moto", disponible=True, lat=10.0, lng=-66.0, calificacion=4.8)
    rep2 = Repartidor(usuario_id=2, vehiculo="Camioneta", disponible=True, lat=10.2, lng=-66.1, calificacion=4.5)
    db.add(rep1)
    db.add(rep2)
    db.commit()

    # 4. Clientes
    cliente1 = Cliente(usuario_id=3, direccion="Calle 5, El Centro", lat=10.1, lng=-66.1, es_institucion=False, exonerado=False)
    cliente2 = Cliente(usuario_id=4, direccion="Av. Principal, frente a la plaza", lat=10.2, lng=-66.2, es_institucion=True, exonerado=True)
    db.add(cliente1)
    db.add(cliente2)
    db.commit()

    # 5. Cilindros (20 cilindros distribuidos)
    planta1 = db.query(Planta).first()
    cilindros_data = []
    for i in range(1, 21):
        tam = random.choice(["P", "M", "G"])
        costo = {"P": 5.0, "M": 10.0, "G": 20.0}[tam]
        precio = {"P": 8.0, "M": 15.0, "G": 30.0}[tam]
        estado = random.choices(["disponible", "disponible", "disponible", "en_ruta"], weights=[70, 20, 10])[0]
        cil = Cilindro(
            codigo_qr=f"CIL-{i:03d}",
            tamanio=tam,
            estado=estado,
            planta_id=planta1.id,
            costo_compra=costo,
            precio_venta=precio
        )
        db.add(cil)
    db.commit()
    print("✅ 20 Cilindros agregados.")

    # 6. Pedidos (10 pedidos con diferentes fechas y estados)
    fechas = [datetime.now() - timedelta(days=i) for i in range(1, 11)]
    estados = ["entregado", "entregado", "entregado", "en_ruta", "pendiente", "entregado", "entregado", "cancelado", "entregado", "entregado"]
    for i in range(10):
        cliente = random.choice([cliente1, cliente2])
        planta = random.choice(plantas)
        repartidor = random.choice([rep1, rep2])
        estado = estados[i]
        monto = round(random.uniform(15, 45), 2)
        ped = Pedido(
            cliente_id=cliente.id,
            repartidor_id=repartidor.id if estado != "pendiente" else None,
            planta_asignada_id=planta.id,
            direccion_entrega=cliente.direccion,
            lat_entrega=cliente.lat,
            lng_entrega=cliente.lng,
            estado=estado,
            costo_logistico=round(random.uniform(0.5, 2.0), 2),
            costo_administrativo=round(random.uniform(0.5, 1.5), 2),
            monto_total=monto,
            fecha_creacion=fechas[i],
            fecha_entrega=fechas[i] + timedelta(hours=random.randint(1, 4)) if estado == "entregado" else None
        )
        db.add(ped)
    db.commit()
    print("✅ 10 Pedidos agregados.")

    # 7. Detalles de pedido (asociar cilindros a pedidos)
    pedidos = db.query(Pedido).all()
    cilindros = db.query(Cilindro).all()
    for ped in pedidos:
        # Cada pedido lleva entre 1 y 3 cilindros
        num_cil = random.randint(1, 3)
        for _ in range(num_cil):
            cil = random.choice(cilindros)
            exonerado = ped.cliente.exonerado if ped.cliente else False
            detalle = DetallePedido(
                pedido_id=ped.id,
                cilindro_id=cil.id,
                cantidad=1,
                precio_unitario=cil.precio_venta if not exonerado else 0,
                exonerado=exonerado
            )
            db.add(detalle)
            # Cambiar estado del cilindro si el pedido está en ruta o entregado
            if ped.estado in ["en_ruta", "entregado"]:
                cil.estado = "vacio" if ped.estado == "entregado" else "en_ruta"
    db.commit()
    print("✅ Detalles de pedidos agregados.")

    # 8. Costos operativos
    costos = [
        CostoOperativo(tipo="Logístico", descripcion="Combustible flota", monto=50.0, fecha=datetime.now() - timedelta(days=2)),
        CostoOperativo(tipo="Administrativo", descripcion="Salario admin", monto=100.0, fecha=datetime.now() - timedelta(days=5)),
        CostoOperativo(tipo="Logístico", descripcion="Mantenimiento moto", monto=30.0, fecha=datetime.now() - timedelta(days=1)),
    ]
    for c in costos:
        db.add(c)
    db.commit()
    print("✅ Costos operativos agregados.")

    db.close()
    print("\n🎉 ¡DATOS CARGADOS EXITOSAMENTE!")

if __name__ == "__main__":
    cargar_datos()
