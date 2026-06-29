from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Numeric, Text
from sqlalchemy.orm import relationship
from .database import Base
import datetime
import enum

class TamanioCilindro(enum.Enum):
    P = "5kg"
    M = "15kg"
    G = "45kg"

class EstadoPedido(enum.Enum):
    pendiente = "pendiente"
    asignado = "asignado"
    en_ruta = "en_ruta"
    entregado = "entregado"
    cancelado = "cancelado"

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    nombre = Column(String)
    telefono = Column(String)
    rol = Column(String)
    fecha_registro = Column(DateTime, default=datetime.datetime.utcnow)

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    usuario = relationship("Usuario")
    direccion = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    es_institucion = Column(Boolean, default=False)
    rif = Column(String, nullable=True)
    exonerado = Column(Boolean, default=False)

class Planta(Base):
    __tablename__ = "plantas"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    capacidad_diaria = Column(Integer)
    direccion = Column(String)

class Repartidor(Base):
    __tablename__ = "repartidores"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    usuario = relationship("Usuario")
    vehiculo = Column(String)
    disponible = Column(Boolean, default=True)
    lat = Column(Float)
    lng = Column(Float)
    calificacion = Column(Float, default=5.0)

class Cilindro(Base):
    __tablename__ = "cilindros"
    id = Column(Integer, primary_key=True, index=True)
    codigo_qr = Column(String, unique=True)
    tamanio = Column(Enum(TamanioCilindro))
    estado = Column(String)
    planta_id = Column(Integer, ForeignKey("plantas.id"))
    planta = relationship("Planta")
    costo_compra = Column(Numeric(10,2))
    precio_venta = Column(Numeric(10,2))

class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    cliente = relationship("Cliente")
    repartidor_id = Column(Integer, ForeignKey("repartidores.id"), nullable=True)
    repartidor = relationship("Repartidor")
    planta_asignada_id = Column(Integer, ForeignKey("plantas.id"))
    planta = relationship("Planta")
    direccion_entrega = Column(String)
    lat_entrega = Column(Float)
    lng_entrega = Column(Float)
    estado = Column(Enum(EstadoPedido), default="pendiente")
    costo_logistico = Column(Numeric(10,2), default=0)
    costo_administrativo = Column(Numeric(10,2), default=0)
    monto_total = Column(Numeric(10,2), default=0)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_entrega = Column(DateTime, nullable=True)

class DetallePedido(Base):
    __tablename__ = "detalles_pedido"
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    pedido = relationship("Pedido")
    cilindro_id = Column(Integer, ForeignKey("cilindros.id"))
    cilindro = relationship("Cilindro")
    cantidad = Column(Integer)
    precio_unitario = Column(Numeric(10,2))
    exonerado = Column(Boolean, default=False)

class CostoOperativo(Base):
    __tablename__ = "costos_operativos"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String)
    descripcion = Column(String)
    monto = Column(Numeric(10,2))
    fecha = Column(DateTime, default=datetime.datetime.utcnow)
