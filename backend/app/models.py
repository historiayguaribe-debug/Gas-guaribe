from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import enum

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

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)  # admin, operativo, auditor, cliente
    nombre_completo = Column(String)

class Proveedor(Base):
    __tablename__ = "proveedores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True)
    direccion = Column(String)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    contacto = Column(String)
    telefono = Column(String)
    precio_P = Column(Float, default=0.0)
    precio_M = Column(Float, default=0.0)
    precio_G = Column(Float, default=0.0)

class Circuito(Base):
    __tablename__ = "circuitos"
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, unique=True)
    nombre = Column(String)
    descripcion = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    comunidades = relationship("Comunidad", back_populates="circuito")

class Comunidad(Base):
    __tablename__ = "comunidades"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    circuito_id = Column(Integer, ForeignKey("circuitos.id"))
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    circuito = relationship("Circuito", back_populates="comunidades")
    clientes = relationship("Cliente", back_populates="comunidad")

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    cedula_rif = Column(String, unique=True)
    telefono = Column(String)
    direccion = Column(String)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    tipo = Column(String, default=TipoCliente.NORMAL.value)
    comunidad_id = Column(Integer, ForeignKey("comunidades.id"))
    comunidad = relationship("Comunidad", back_populates="clientes")
    ventas = relationship("Venta", back_populates="cliente")
    pedidos = relationship("Pedido", back_populates="cliente")

class Cilindro(Base):
    __tablename__ = "cilindros"
    id = Column(Integer, primary_key=True, index=True)
    codigo_qr = Column(String, unique=True, index=True)
    tamano = Column(String)
    estado = Column(String, default=EstadoCilindro.DISPONIBLE.value)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"))
    costo_compra = Column(Float)
    precio_venta = Column(Float)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    proveedor = relationship("Proveedor")

class Carga(Base):
    __tablename__ = "cargas"
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"))
    cantidad_P = Column(Integer, default=0)
    cantidad_M = Column(Integer, default=0)
    cantidad_G = Column(Integer, default=0)
    costo_total = Column(Float)
    numero_factura = Column(String)
    gastos_logisticos = Column(Float, default=0.0)
    proveedor = relationship("Proveedor")

class Venta(Base):
    __tablename__ = "ventas"
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, default=datetime.utcnow)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"))
    tamano = Column(String)
    cantidad = Column(Integer)
    precio_unitario = Column(Float)
    exonerado = Column(Boolean, default=False)
    cliente = relationship("Cliente", back_populates="ventas")
    proveedor = relationship("Proveedor")

class GastoOperativo(Base):
    __tablename__ = "gastos_operativos"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String)
    descripcion = Column(String)
    monto = Column(Float)
    fecha = Column(DateTime, default=datetime.utcnow)

class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    fecha = Column(DateTime, default=datetime.utcnow)
    estado = Column(String, default="pendiente")
    tamano = Column(String)
    cantidad = Column(Integer)
    precio_unitario = Column(Float, default=0.0)
    exonerado = Column(Boolean, default=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    cliente = relationship("Cliente", back_populates="pedidos")
    proveedor = relationship("Proveedor")
