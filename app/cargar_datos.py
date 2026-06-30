from sqlalchemy.orm import Session
from .models import (
    Usuario, Proveedor, Circuito, Comunidad, Cliente, Cilindro,
    Carga, Venta, GastoOperativo, Pedido
)
from .auth import get_password_hash
from .utils import generar_codigo_qr
from datetime import datetime, timedelta
import random


def cargar_datos_iniciales(db: Session):
    """
    Carga datos de prueba en la base de datos si está vacía.
    """
    # Si ya hay usuarios, asumimos que la base de datos ya fue inicializada
    if db.query(Usuario).count() > 0:
        return

    # ---------- USUARIOS ----------
    usuarios = [
        Usuario(
            username="admin",
            hashed_password=get_password_hash("admin.gas2026"),
            role="admin",
            nombre_completo="Administrador Principal"
        ),
        Usuario(
            username="oper1",
            hashed_password=get_password_hash("1234"),
            role="operativo",
            nombre_completo="Operativo 1"
        ),
        Usuario(
            username="oper2",
            hashed_password=get_password_hash("1234"),
            role="operativo",
            nombre_completo="Operativo 2"
        ),
        Usuario(
            username="auditor1",
            hashed_password=get_password_hash("1234"),
            role="auditor",
            nombre_completo="Auditor 1"
        ),
        Usuario(
            username="auditor2",
            hashed_password=get_password_hash("1234"),
            role="auditor",
            nombre_completo="Auditor 2"
        ),
    ]
    db.add_all(usuarios)
    db.commit()

    # ---------- PROVEEDORES ----------
    proveedores_data = [
        {
            "nombre": "Planta Altagracia de Orituco",
            "direccion": "Av. Principal, Altagracia",
            "contacto": "Juan Pérez",
            "telefono": "0412-1234567",
            "precio_P": 15.0,
            "precio_M": 25.0,
            "precio_G": 35.0
        },
        {
            "nombre": "Planta Valle de la Pascua",
            "direccion": "Calle 5, Valle de la Pascua",
            "contacto": "María Gómez",
            "telefono": "0416-7654321",
            "precio_P": 14.5,
            "precio_M": 24.0,
            "precio_G": 34.0
        },
        {
            "nombre": "Planta Puerto La Cruz",
            "direccion": "Av. Municipal, Puerto La Cruz",
            "contacto": "Carlos López",
            "telefono": "0424-9876543",
            "precio_P": 16.0,
            "precio_M": 26.0,
            "precio_G": 36.0
        },
    ]
    proveedores = []
    for p in proveedores_data:
        prov = Proveedor(**p)
        db.add(prov)
        proveedores.append(prov)
    db.commit()

    # ---------- CIRCUITOS (I al IX) ----------
    circuitos_nombres = [
        "Circuito I", "Circuito II", "Circuito III", "Circuito IV",
        "Circuito V", "Circuito VI", "Circuito VII", "Circuito VIII",
        "Circuito IX"
    ]
    circuitos = []
    for i, nombre in enumerate(circuitos_nombres, start=1):
        c = Circuito(
            numero=i,
            nombre=nombre,
            descripcion=f"Circuito comunal {i}"
        )
        db.add(c)
        circuitos.append(c)
    db.commit()

    # ---------- COMUNIDADES (40 ejemplos) ----------
    comunidades_nombres = [
        "Barrio Bella Vista", "Urbanización Los Robles", "Sector El Carmen",
        "La Floresta", "Los Pinos", "El Mango", "Las Acacias", "Santa Rosa",
        "Villa Olímpica", "Los Sauces", "El Paraíso", "La Loma",
        "Las Brisas", "El Valle", "Las Mercedes", "Los Almendros",
        "El Cují", "La Morita", "San José", "Los Jardines",
        "El Prado", "Las Palmas", "La Campiña", "Los Rosales",
        "El Manantial", "La Hacienda", "Los Angeles", "San Miguel",
        "El Rosario", "La Aurora", "El Horizonte", "Las Flores",
        "Los Olivos", "El Sol", "Las Dunas", "Los Cerezos",
        "El Mirador", "La Esperanza", "Los Nogales", "El Remanso"
    ]
    for nombre in comunidades_nombres[:40]:
        circuito = random.choice(circuitos)
        com = Comunidad(nombre=nombre, circuito_id=circuito.id)
        db.add(com)
    db.commit()

    comunidades = db.query(Comunidad).all()

    # ---------- CLIENTE DE PRUEBA (para el usuario cliente) ----------
    cliente_prueba = Cliente(
        nombre="Cliente Prueba",
        cedula_rif="V-1234567",
        telefono="0412-0000000",
        direccion="Calle Principal, Comunidad Ejemplo",
        tipo="Normal",
        comunidad_id=random.choice(comunidades).id
    )
    db.add(cliente_prueba)
    db.commit()

    # Usuario cliente asociado a ese cliente
    user_cliente = Usuario(
        username="V-1234567",
        hashed_password=get_password_hash("cliente123"),
        role="cliente",
        nombre_completo="Cliente Prueba"
    )
    db.add(user_cliente)
    db.commit()

    # ---------- MÁS CLIENTES (9 adicionales) ----------
    for i in range(9):
        cliente = Cliente(
            nombre=f"Cliente {i+2}",
            cedula_rif=f"V-{random.randint(1000000, 9999999)}",
            telefono=f"0412-{random.randint(1000000, 9999999)}",
            direccion=f"Calle {i+1}, {random.choice(comunidades).nombre}",
            tipo="Institución Exonerada" if i % 3 == 0 else "Normal",
            comunidad_id=random.choice(comunidades).id
        )
        db.add(cliente)
    db.commit()

    # ---------- CILINDROS (20) ----------
    tamano_opciones = ["P", "M", "G"]
    for _ in range(20):
        tam = random.choice(tamano_opciones)
        proveedor = random.choice(proveedores)
        costo = getattr(proveedor, f"precio_{tam}")
        cil = Cilindro(
            codigo_qr=generar_codigo_qr(),
            tamano=tam,
            estado=random.choice(["disponible", "en ruta", "vacio", "mantenimiento"]),
            proveedor_id=proveedor.id,
            costo_compra=costo,
            precio_venta=costo * 1.3
        )
        db.add(cil)
    db.commit()

    # ---------- CARGAS (3) ----------
    for _ in range(3):
        prov = random.choice(proveedores)
        cant_P = random.randint(5, 15)
        cant_M = random.randint(3, 10)
        cant_G = random.randint(2, 8)
        costo = (
            cant_P * prov.precio_P +
            cant_M * prov.precio_M +
            cant_G * prov.precio_G
        )
        carga = Carga(
            fecha=datetime.utcnow() - timedelta(days=random.randint(0, 10)),
            proveedor_id=prov.id,
            cantidad_P=cant_P,
            cantidad_M=cant_M,
            cantidad_G=cant_G,
            costo_total=costo,
            numero_factura=f"FAC-{random.randint(1000,9999)}",
            gastos_logisticos=random.uniform(20, 100)
        )
        db.add(carga)
    db.commit()

    # ---------- VENTAS (10) ----------
    clientes = db.query(Cliente).all()
    for _ in range(10):
        cliente = random.choice(clientes)
        tam = random.choice(tamano_opciones)
        cant = random.randint(1, 5)
        precio = random.uniform(15, 35)
        exonerado = cliente.tipo == "Institución Exonerada"
        venta = Venta(
            fecha=datetime.utcnow() - timedelta(days=random.randint(0, 5)),
            cliente_id=cliente.id,
            proveedor_id=random.choice(proveedores).id,
            tamano=tam,
            cantidad=cant,
            precio_unitario=0 if exonerado else precio,
            exonerado=exonerado
        )
        db.add(venta)
    db.commit()

    # ---------- PEDIDOS (5) ----------
    for _ in range(5):
        cl = random.choice(clientes)
        tam = random.choice(["P", "M", "G"])
        cant = random.randint(1, 4)
        ped = Pedido(
            cliente_id=cl.id,
            fecha=datetime.utcnow() - timedelta(days=random.randint(0, 3)),
            estado=random.choice(["pendiente", "en_ruta", "entregado"]),
            tamano=tam,
            cantidad=cant,
            exonerado=cl.tipo == "Institución Exonerada",
            proveedor_id=random.choice(proveedores).id
        )
        db.add(ped)
    db.commit()

    # ---------- GASTOS OPERATIVOS (3) ----------
    gastos_data = [
        {"tipo": "Logístico", "descripcion": "Combustible para transporte", "monto": 150.0},
        {"tipo": "Administrativo", "descripcion": "Pago de salarios", "monto": 800.0},
        {"tipo": "Logístico", "descripcion": "Mantenimiento de vehículos", "monto": 200.0},
    ]
    for g in gastos_data:
        gasto = GastoOperativo(
            tipo=g["tipo"],
            descripcion=g["descripcion"],
            monto=g["monto"],
            fecha=datetime.utcnow() - timedelta(days=random.randint(0, 3))
        )
        db.add(gasto)
    db.commit()
