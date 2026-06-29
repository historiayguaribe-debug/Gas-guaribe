from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Numeric, Text
from sqlalchemy.orm import relationship
from .database import Base
import datetime
import enum

# Definimos los tamaños de los cilindros
class TamanioCilindro(enum.Enum):
    P = "5kg"
    M = "15kg"
    G = "45kg"

# Definimos los estados de un pedido
class EstadoPedido(enum.Enum):
    pendiente = "pendiente"
    asignado = "asignado"
    en_ruta = "en_ruta"
    entregado = "entregado"
    cancelado = "cancelado"

# --- TABLA DE USUARIOS ---
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    nombre = Column(String)
    telefono = Column(String)
    rol = Column(String)  # cliente, repartidor, admin
    fecha_registro = Column(DateTime, default=datetime.datetime.utcnow)

    # Relaciones
    cliente = relationship("Cliente", back_populates="usuario", uselist=False)
    repartidor = relationship("Repartidor", back_populates="usuario", uselist=False)

# --- TABLA DE CLIENTES ---
class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    direccion = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    es_institucion = Column(Boolean, default=False)
    rif = Column(String, nullable=True)
    exonerado = Column(Boolean, default=False)

    # Relaciones
    usuario = relationship("Usuario", back_populates="cliente")
    pedidos = relationship("Pedido", back_populates="cliente_rel")

# --- TABLA DE PLANTAS ---
class Planta(Base):
    __tablename__ = "plantas"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    capacidad_diaria = Column(Integer)
    direccion = Column(String)

# --- TABLA DE REPARTIDORES ---
class Repartidor(Base):
    __tablename__ = "repartidores"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    vehiculo = Column(String)
    disponible = Column(Boolean, default=True)
    lat = Column(Float)
    lng = Column(Float)
    calificacion = Column(Float, default=5.0)

    usuario = relationship("Usuario", back_populates="repartidor")

# --- TABLA DE CILINDROS ---
class Cilindro(Base):
    __tablename__ = "cilindros"
    id = Column(Integer, primary_key=True, index=True)
    codigo_qr = Column(String, unique=True)
    tamanio = Column(Enum(TamanioCilindro))
    estado = Column(String)  # disponible, en_ruta, vacio
    planta_id = Column(Integer, ForeignKey("plantas.id"))
    costo_compra = Column(Numeric(10,2))
    precio_venta = Column(Numeric(10,2))

# --- TABLA DE PEDIDOS ---
class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    repartidor_id = Column(Integer, ForeignKey("repartidores.id"), nullable=True)
    planta_asignada_id = Column(Integer, ForeignKey("plantas.id"))
    direccion_entrega = Column(String)
    lat_entrega = Column(Float)
    lng_entrega = Column(Float)
    estado = Column(Enum(EstadoPedido), default="pendiente")
    costo_logistico = Column(Numeric(10,2), default=0)
    costo_administrativo = Column(Numeric(10,2), default=0)
    monto_total = Column(Numeric(10,2), default=0)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_entrega = Column(DateTime, nullable=True)

    # Relaciones
    cliente_rel = relationship("Cliente", back_populates="pedidos")
    detalles = relationship("DetallePedido", back_populates="pedido_rel")

# --- TABLA DE DETALLE DEL PEDIDO ---
class DetallePedido(Base):
    __tablename__ = "detalles_pedido"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    cilindro_id = Column(Integer, ForeignKey("cilindros.id"))
    cantidad = Column(Integer)
    precio_unitario = Column(Numeric(10,2))
    exonerado = Column(Boolean, default=False)

    # Relaciones
    pedido_rel = relationship("Pedido", back_populates="detalles")
    cilindro = relationship("Cilindro")

# --- TABLA DE COSTOS OPERATIVOS ---
class CostoOperativo(Base):
    __tablename__ = "costos_operativos"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String)  # Logístico, Administrativo
    descripcion = Column(String)
    monto = Column(Numeric(10,2))
    fecha = Column(DateTime, default=datetime.datetime.utcnow)
