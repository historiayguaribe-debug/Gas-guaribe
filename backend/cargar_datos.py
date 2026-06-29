from app.database import SessionLocal
from app.models import Planta, Repartidor, Usuario, Cliente
from app.auth import hash_password
import sys

def cargar():
    db = SessionLocal()
    
    # Verificar si ya hay datos para no duplicar
    if db.query(Planta).count() > 0:
        print("⚠️  Ya existen datos en la base. No se cargarán duplicados.")
        db.close()
        return

    print("🔄 Cargando datos de prueba...")

    # 1. Agregar las 3 plantas de llenado
    plantas = [
        Planta(nombre="Altagracia de Orituco", lat=9.8667, lng=-66.3833, capacidad_diaria=200, direccion="Calle Principal, Altagracia"),
        Planta(nombre="Valle de la Pascua", lat=9.2000, lng=-66.0000, capacidad_diaria=150, direccion="Av. Bolívar, Valle de la Pascua"),
        Planta(nombre="Puerto La Cruz", lat=10.2167, lng=-64.6167, capacidad_diaria=300, direccion="Zona Industrial, Puerto La Cruz")
    ]
    for p in plantas:
        db.add(p)
    db.commit()
    print("✅ 3 Plantas agregadas.")

    # 2. Crear un repartidor de prueba
    usuario_rep = Usuario(
        email="repartidor1@test.com", 
        hashed_password=hash_password("1234"), 
        nombre="Juan Perez", 
        telefono="0412-1234567", 
        rol="repartidor"
    )
    db.add(usuario_rep)
    db.commit()
    repartidor = Repartidor(
        usuario_id=usuario_rep.id, 
        vehiculo="Moto", 
        disponible=True, 
        lat=10.0, 
        lng=-66.0, 
        calificacion=5.0
    )
    db.add(repartidor)
    db.commit()
    print("✅ Repartidor 'Juan Perez' creado.")

    # 3. Crear un cliente normal
    user_cli = Usuario(
        email="cliente@test.com", 
        hashed_password=hash_password("1234"), 
        nombre="Maria Gomez", 
        telefono="0412-9876543", 
        rol="cliente"
    )
    db.add(user_cli)
    db.commit()
    cliente = Cliente(
        usuario_id=user_cli.id, 
        direccion="Calle 5, El Centro", 
        lat=10.1, 
        lng=-66.1, 
        es_institucion=False,
        exonerado=False
    )
    db.add(cliente)
    db.commit()
    print("✅ Cliente 'Maria Gomez' creado.")

    # 4. Crear una escuela (exonerada)
    user_esc = Usuario(
        email="escuela@test.com", 
        hashed_password=hash_password("1234"), 
        nombre="Escuela Bolivariana", 
        telefono="0412-1111111", 
        rol="cliente"
    )
    db.add(user_esc)
    db.commit()
    escuela = Cliente(
        usuario_id=user_esc.id, 
        direccion="Av. Principal, frente a la plaza", 
        lat=10.2, 
        lng=-66.2, 
        es_institucion=True,
        exonerado=True  # <- Esta es la escuela que no paga
    )
    db.add(escuela)
    db.commit()
    print("✅ Escuela exonerada creada.")

    # 5. (Opcional) Agregar algunos cilindros de prueba a la primera planta
    from app.models import Cilindro, TamanioCilindro
    planta1 = db.query(Planta).first()
    cilindros = [
        Cilindro(codigo_qr="CIL-001", tamanio=TamanioCilindro.P, estado="disponible", planta_id=planta1.id, costo_compra=5.00, precio_venta=8.00),
        Cilindro(codigo_qr="CIL-002", tamanio=TamanioCilindro.M, estado="disponible", planta_id=planta1.id, costo_compra=10.00, precio_venta=15.00),
        Cilindro(codigo_qr="CIL-003", tamanio=TamanioCilindro.G, estado="disponible", planta_id=planta1.id, costo_compra=20.00, precio_venta=30.00),
        Cilindro(codigo_qr="CIL-004", tamanio=TamanioCilindro.M, estado="disponible", planta_id=planta1.id, costo_compra=10.00, precio_venta=15.00),
    ]
    for c in cilindros:
        db.add(c)
    db.commit()
    print("✅ 4 Cilindros de prueba agregados.")

    db.close()
    print("\n🎉 ¡DATOS CARGADOS EXITOSAMENTE!")
    print("Usuarios creados:")
    print("  - repartidor1@test.com / 1234")
    print("  - cliente@test.com / 1234")
    print("  - escuela@test.com / 1234")

if __name__ == "__main__":
    cargar()
