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
    Esta función se ejecuta automáticamente al iniciar la aplicación.
    """
    db = SessionLocal()

    # Verificar si ya hay datos (para no duplicar)
    if db.query(Usuario).count() > 0:
        print("⚠️  La base de datos ya contiene información. No se cargarán datos de prueba.")
        db.close()
        return

    print("🔄 Cargando datos de prueba para GASGUARIBE...")

    # --- 1. PLANTAS DE LLENADO ---
    plantas = [
        Planta(
            nombre="Altagracia de Orituco",
            lat=9.8667,
            lng=-66.3833,
            capacidad_diaria=200,
            direccion="Calle Principal, Altagracia"
        ),
        Planta(
            nombre="Valle de la Pascua",
            lat=9.2000,
            lng=-66.0000,
            capacidad_diaria=150,
            direccion="Av. Bolívar, Valle de la Pascua"
        ),
        Planta(
            nombre="Puerto La Cruz",
            lat=10.2167,
            lng=-64.6167,
            capacidad_diaria=300,
            direccion="Zona Industrial, Puerto La Cruz"
        )
    ]
    for p in plantas:
        db.add(p)
    db.commit()
    print("✅ 3 Plantas de llenado agregadas.")

    # --- 2. USUARIOS (repartidores, clientes, admin) ---
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
    print("✅ 5 Usuarios creados (2 repartidores, 2 clientes, 1 admin).")

    # --- 3. REPARTIDORES (asociados a los usuarios) ---
    rep1 = Repartidor(
        usuario_id=usuarios_creados[0].id,  # repartidor1
        vehiculo="Moto",
        disponible=True,
        lat=10.0,
        lng=-66.0,
        calificacion=4.8
    )
    rep2 = Repartidor(
        usuario_id=usuarios_creados[1].id,  # repartidor2
        vehiculo="Camioneta",
        disponible=True,
        lat=10.2,
        lng=-66.1,
        calificacion=4.5
    )
    db.add(rep1)
    db.add(rep2)
    db.commit()
    print("✅ 2 Repartidores agregados.")

    # --- 4. CLIENTES (normal y exonerado) ---
    cliente_normal = Cliente(
        usuario_id=usuarios_creados[2].id,  # cliente@test.com
        direccion="Calle 5, El Centro",
        lat=10.1,
        lng=-66.1,
        es_institucion=False,
        exonerado=False
    )
    cliente_exonerado = Cliente(
        usuario_id=usuarios_creados[3].id,  # escuela@test.com
        direccion="Av. Principal, frente a la plaza",
        lat=10.2,
        lng=-66.2,
        es_institucion=True,
        exonerado=True
    )
    db.add(cliente_normal)
    db.add(cliente_exonerado)
    db.commit()
    print("✅ 2 Clientes agregados (1 normal, 1 exonerado).")

    # --- 5. CILINDROS (20 cilindros de diferentes tamaños y estados) ---
    planta_principal = db.query(Planta).first()
    cilindros_creados = []
    for i in range(1, 21):
        # Elegir tamaño aleatorio
        tam = random.choice(["P", "M", "G"])
        costo = {"P": 5.0, "M": 10.0, "G": 20.0}[tam]
        precio = {"P": 8.0, "M": 15.0, "G": 30.0}[tam]
        # Estados: mayoría disponibles, algunos en ruta o vacíos
        estado = random.choices(
            ["disponible", "disponible", "disponible", "en_ruta", "vacio"],
            weights=[60, 20, 10, 5, 5]
        )[0]
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

    # --- 6. PEDIDOS (10 pedidos con diferentes fechas y estados) ---
    estados_pedido = ["entregado", "entregado", "entregado", "en_ruta", "pendiente",
                      "entregado", "entregado", "cancelado", "entregado", "entregado"]
    fechas = [datetime.now() - timedelta(days=i) for i in range(10)]
    pedidos_creados = []

    for i in range(10):
        cliente = random.choice([cliente_normal, cliente_exonerado])
        planta = random.choice(plantas)
        repartidor = random.choice([rep1, rep2]) if estados_pedido[i] != "pendiente" else None
        estado = estados_pedido[i]
        monto_base = random.uniform(15, 45)  # será ajustado por los detalles

        ped = Pedido(
            cliente_id=cliente.id,
            repartidor_id=repartidor.id if repartidor else None,
            planta_asignada_id=planta.id,
            direccion_entrega=cliente.direccion,
            lat_entrega=cliente.lat,
            lng_entrega=cliente.lng,
            estado=estado,
            costo_logistico=round(random.uniform(0.5, 2.5), 2),
            costo_administrativo=round(random.uniform(0.5, 1.5), 2),
            monto_total=0,  # se calculará después con los detalles
            fecha_creacion=fechas[i],
            fecha_entrega=fechas[i] + timedelta(hours=random.randint(1, 4)) if estado == "entregado" else None
        )
        db.add(ped)
        db.commit()
        db.refresh(ped)
        pedidos_creados.append(ped)

    print("✅ 10 Pedidos creados.")

    # --- 7. DETALLES DE PEDIDOS (asignar cilindros a cada pedido) ---
    for ped in pedidos_creados:
        # Cada pedido lleva entre 1 y 3 cilindros
        num_cilindros = random.randint(1, 3)
        cilindros_seleccionados = random.sample(cilindros_creados, num_cilindros)
        total_pedido = 0
        for cil in cilindros_seleccionados:
            exonerado = ped.cliente.exonerado if ped.cliente else False
            precio_unitario = cil.precio_venta if not exonerado else 0
            total_pedido += precio_unitario
            detalle = DetallePedido(
                pedido_id=ped.id,
                cilindro_id=cil.id,
                cantidad=1,
                precio_unitario=precio_unitario,
                exonerado=exonerado
            )
            db.add(detalle)
            # Actualizar estado del cilindro si el pedido está en ruta o entregado
            if ped.estado in ["en_ruta", "entregado"]:
                cil.estado = "vacio" if ped.estado == "entregado" else "en_ruta"
        # Actualizar el monto total del pedido
        ped.monto_total = round(total_pedido, 2)
    db.commit()
    print("✅ Detalles de pedidos agregados y montos actualizados.")

    # --- 8. COSTOS OPERATIVOS (gastos de la empresa) ---
    costos = [
        CostoOperativo(
            tipo="Logístico",
            descripcion="Combustible flota (semana)",
            monto=50.0,
            fecha=datetime.now() - timedelta(days=2)
        ),
        CostoOperativo(
            tipo="Administrativo",
            descripcion="Salario personal administrativo (quincena)",
            monto=100.0,
            fecha=datetime.now() - timedelta(days=5)
        ),
        CostoOperativo(
            tipo="Logístico",
            descripcion="Mantenimiento de motos",
            monto=30.0,
            fecha=datetime.now() - timedelta(days=1)
        ),
        CostoOperativo(
            tipo="Administrativo",
            descripcion="Pago de oficina (luz, agua, internet)",
            monto=25.0,
            fecha=datetime.now() - timedelta(days=3)
        ),
    ]
    for c in costos:
        db.add(c)
    db.commit()
    print("✅ 4 Costos operativos agregados.")

    db.close()
    print("\n🎉 ¡DATOS DE PRUEBA CARGADOS EXITOSAMENTE!")
    print("📊 Resumen:")
    print(f"   - {len(plantas)} Plantas de llenado")
    print(f"   - {len(usuarios_creados)} Usuarios")
    print(f"   - 2 Repartidores")
    print(f"   - 2 Clientes (1 exonerado)")
    print(f"   - {len(cilindros_creados)} Cilindros")
    print(f"   - {len(pedidos_creados)} Pedidos")
    print(f"   - {len(costos)} Costos operativos")
    print("\n🔑 Credenciales de prueba:")
    print("   - repartidor1@test.com / 1234")
    print("   - repartidor2@test.com / 1234")
    print("   - cliente@test.com / 1234")
    print("   - escuela@test.com / 1234")
    print("   - admin@test.com / 1234")

if __name__ == "__main__":
    cargar_datos()
