from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import enum


# ---------- ENUMS ----------
class TamanoCilindro(str, enum.Enum):
    P = "P"
    M = "M"
    G = "G"


class EstadoCilindro(str, enum.Enum):
    DISPONIBLE = "disponible"
    EN_RUTA = "en ruta"
    VACIO = "vacio"
    MANTENIMIENTO = "mantenimiento"


class TipoCliente(str, enum.Enum):
    NORMAL = "Normal"
    INSTITUCION_EXONERADA = "Institución Exonerada"


class TipoGasto(str, enum.Enum):
    LOGISTICO = "Logístico"
    ADMINISTRATIVO = "Administrativo"


# ---------- TABLAS ----------
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # admin, operativo, auditor, cliente
    nombre_completo = Column(String, nullable=False)


class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    direccion = Column(String)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    contacto = Column(String)
    telefono = Column(String)
    precio_P = Column(Float, default=0.0)
    precio_M = Column(Float, default=0.0)
    precio_G = Column(Float, default=0.0)

    # Relaciones
    cargas = relationship("Carga", back_populates="proveedor")
    cilindros = relationship("Cilindro", back_populates="proveedor")
    ventas = relationship("Venta", back_populates="proveedor")


class Circuito(Base):
    __tablename__ = "circuitos"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    # Relaciones
    comunidades = relationship("Comunidad", back_populates="circuito", cascade="all, delete-orphan")


class Comunidad(Base):
    __tablename__ = "comunidades"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    circuito_id = Column(Integer, ForeignKey("circuitos.id"), nullable=False)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    # Relaciones
    circuito = relationship("Circuito", back_populates="comunidades")
    clientes = relationship("Cliente", back_populates="comunidad", cascade="all, delete-orphan")


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    cedula_rif = Column(String, unique=True, nullable=False)
    telefono = Column(String)
    direccion = Column(String)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    tipo = Column(Enum(TipoCliente), default=TipoCliente.NORMAL)
    comunidad_id = Column(Integer, ForeignKey("comunidades.id"), nullable=False)

    # Relaciones
    comunidad = relationship("Comunidad", back_populates="clientes")
    ventas = relationship("Venta", back_populates="cliente")
    pedidos = relationship("Pedido", back_populates="cliente")


class Cilindro(Base):
    __tablename__ = "cilindros"

    id = Column(Integer, primary_key=True, index=True)
    codigo_qr = Column(String, unique=True, index=True, nullable=False)
    tamano = Column(Enum(TamanoCilindro), nullable=False)
    estado = Column(Enum(EstadoCilindro), default=EstadoCilindro.DISPONIBLE)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    costo_compra = Column(Float, nullable=False)
    precio_venta = Column(Float, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    proveedor = relationship("Proveedor", back_populates="cilindros")


class Carga(Base):
    __tablename__ = "cargas"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    cantidad_P = Column(Integer, default=0)
    cantidad_M = Column(Integer, default=0)
    cantidad_G = Column(Integer, default=0)
    costo_total = Column(Float, nullable=False)
    numero_factura = Column(String, nullable=False)
    gastos_logisticos = Column(Float, default=0.0)

    # Relaciones
    proveedor = relationship("Proveedor", back_populates="cargas")


class Venta(Base):
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    tamano = Column(Enum(TamanoCilindro), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    exonerado = Column(Boolean, default=False)

    # Relaciones
    cliente = relationship("Cliente", back_populates="ventas")
    proveedor = relationship("Proveedor", back_populates="ventas")


class GastoOperativo(Base):
    __tablename__ = "gastos_operativos"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(Enum(TipoGasto), nullable=False)
    descripcion = Column(String, nullable=False)
    monto = Column(Float, nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)
    estado = Column(String, default="pendiente")  # pendiente, en_ruta, entregado, cancelado
    tamano = Column(Enum(TamanoCilindro), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, default=0.0)
    exonerado = Column(Boolean, default=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)

    # Relaciones
    cliente = relationship("Cliente", back_populates="pedidos")
    proveedor = relationship("Proveedor")
