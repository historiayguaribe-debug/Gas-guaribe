from .database import SessionLocal
from .models import (
    Planta, Repartidor, Usuario, Cliente, Cilindro,
    TamanioCilindro, Pedido, DetallePedido, CostoOperativo
)
from .auth import hash_password
from datetime import datetime, timedelta
import random

def cargar_datos():
    """
    Carga datos de prueba en la base de datos si está vacía.
    """
    db = SessionLocal()

    if db.query(Usuario).count() > 0:
        print("⚠️ La base de datos ya contiene información. No se cargarán datos de prueba.")
        db.close()
        return

    print("🔄 Cargando datos de prueba para GASGUARIBE...")

    # --- 1. PLANTAS ---
    plantas = [
        Planta(nombre="Altagracia de Orituco", lat=9.8667, lng=-66.3833, capacidad_diaria=200, direccion="Calle Principal, Altagracia"),
        Planta(nombre="Valle de la Pascua", lat=9.2000, lng=-66.0000, capacidad_diaria=150, direccion="Av. Bolívar, Valle de la Pascua"),
        Planta(nombre="Puerto La Cruz", lat=10.2167, lng=-64.6167, capacidad_diaria=300, direccion="Zona Industrial, Puerto La Cruz")
    ]
    db.add_all(plantas)
    db.commit()
    print("✅ 3 Plantas de llenado agregadas.")

    # --- 2. USUARIOS ---
    usuarios_data = [
        {"email": "repartidor1@test.com", "password": "1234", "nombre": "Juan Pérez", "telefono": "0412-1234567", "rol": "repartidor"},
        {"email": "repartidor2@test.com", "password": "1234", "nombre": "María López", "telefono": "0412-2345678", "rol": "repartidor"},
        {"email": "cliente@test.com", "password": "1234", "nombre": "Carlos Gómez", "telefono": "0412-9876543", "rol": "cliente"},
        {"email": "escuela@test.com", "password": "1234", "nombre": "Escuela Bolivariana", "telefono": "0412-1111111", "rol": "cliente"},
        {"email": "admin@test.com", "password": "1234", "nombre": "Admin Guaribe", "telefono": "0412-0000000", "rol": "admin"},
    ]
    usuarios_creados = []
    for u in usuarios_data:
        user = Usuario(
            email=u["email"],
            hashed_password=hash_password(u["password"]),
            nombre=u["nombre"],
            telefono=u["telefono"],
            rol=u["rol"]
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        usuarios_creados.append(user)
    print("✅ 5 Usuarios creados.")

    # --- 3. REPARTIDORES ---
    rep1 = Repartidor(usuario_id=usuarios_creados[0].id, vehiculo="Moto", disponible=True, lat=10.0, lng=-66.0, calificacion=4.8)
    rep2 = Repartidor(usuario_id=usuarios_creados[1].id, vehiculo="Camioneta", disponible=True, lat=10.2, lng=-66.1, calificacion=4.5)
    db.add_all([rep1, rep2])
    db.commit()
    print("✅ 2 Repartidores agregados.")

    # --- 4. CLIENTES ---
    cliente_normal = Cliente(usuario_id=usuarios_creados[2].id, direccion="Calle 5, El Centro", lat=10.1, lng=-66.1, es_institucion=False, exonerado=False)
    cliente_exonerado = Cliente(usuario_id=usuarios_creados[3].id, direccion="Av. Principal, frente a la plaza", lat=10.2, lng=-66.2, es_institucion=True, exonerado=True)
    db.add_all([cliente_normal, cliente_exonerado])
    db.commit()
    print("✅ 2 Clientes agregados (1 normal, 1 exonerado).")

    # --- 5. CILINDROS ---
    planta_principal = db.query(Planta).first()
    cilindros_creados = []
    for i in range(1, 21):
        tam = random.choice(["P", "M", "G"])
        costo = {"P": 5.0, "M": 10.0, "G": 20.0}[tam]
        precio = {"P": 8.0, "M": 15.0, "G": 30.0}[tam]
        estado = random.choices(["disponible", "disponible", "disponible", "en_ruta", "vacio"], weights=[60, 20, 10, 5, 5])[0]
        cil = Cilindro(
            codigo_qr=f"CIL-{i:03d}",
            tamanio=tam,
            estado=estado,
            planta_id=planta_principal.id,
            costo_compra=costo,
            precio_venta=precio
        )
        db.add(cil)
        cilindros_creados.append(cil)
    db.commit()
    print("✅ 20 Cilindros agregados.")

    # --- 6. PEDIDOS Y DETALLES ---
    estados_pedido = ["entregado", "entregado", "entregado", "en_ruta", "pendiente",
                      "entregado", "entregado", "cancelado", "entregado", "entregado"]
    fechas = [datetime.now() - timedelta(days=i) for i in range(10)]
    clientes = [cliente_normal, cliente_exonerado]

    for i in range(10):
        cliente = random.choice(clientes)
        planta = random.choice(plantas)
        repartidor = random.choice([rep1, rep2]) if estados_pedido[i] != "pendiente" else None
        estado = estados_pedido[i]

        pedido = Pedido(
            cliente_id=cliente.id,
            repartidor_id=repartidor.id if repartidor else None,
            planta_asignada_id=planta.id,
            direccion_entrega=cliente.direccion,
            lat_entrega=cliente.lat,
            lng_entrega=cliente.lng,
            estado=estado,
            costo_logistico=round(random.uniform(0.5, 2.5), 2),
            costo_administrativo=round(random.uniform(0.5, 1.5), 2),
            monto_total=0,
            fecha_creacion=fechas[i],
            fecha_entrega=fechas[i] + timedelta(hours=random.randint(1, 4)) if estado == "entregado" else None
        )
        db.add(pedido)
        db.commit()
        db.refresh(pedido)

        # Crear detalles del pedido
        num_cilindros = random.randint(1, 3)
        cilindros_seleccionados = random.sample(cilindros_creados, num_cilindros)
        total_pedido = 0
        for cil in cilindros_seleccionados:
            exonerado = cliente.exonerado
            precio_unitario = cil.precio_venta if not exonerado else 0
            total_pedido += precio_unitario
            detalle = DetallePedido(
                pedido_id=pedido.id,
                cilindro_id=cil.id,
                cantidad=1,
                precio_unitario=precio_unitario,
                exonerado=exonerado
            )
            db.add(detalle)
            if estado in ["en_ruta", "entregado"]:
                cil.estado = "vacio" if estado == "entregado" else "en_ruta"
        pedido.monto_total = round(total_pedido, 2)
        db.commit()

    print("✅ 10 Pedidos y sus detalles creados.")

    # --- 7. COSTOS OPERATIVOS ---
    costos = [
        CostoOperativo(tipo="Logístico", descripcion="Combustible flota (semana)", monto=50.0, fecha=datetime.now() - timedelta(days=2)),
        CostoOperativo(tipo="Administrativo", descripcion="Salario personal administrativo (quincena)", monto=100.0, fecha=datetime.now() - timedelta(days=5)),
        CostoOperativo(tipo="Logístico", descripcion="Mantenimiento de motos", monto=30.0, fecha=datetime.now() - timedelta(days=1)),
    ]
    db.add_all(costos)
    db.commit()
    print("✅ 3 Costos operativos agregados.")

    db.close()
    print("\n🎉 ¡DATOS DE PRUEBA CARGADOS EXITOSAMENTE!")

if __name__ == "__main__":
    cargar_datos()
