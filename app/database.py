from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

db_url = settings.DATABASE_URL if settings.DATABASE_URL else "sqlite:///./gas_guaribe.db"

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Importar modelos para registrar las tablas
from .models import Usuario, Proveedor, Circuito, Comunidad, Cliente, Cilindro, Carga, Venta, GastoOperativo, Pedido

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
