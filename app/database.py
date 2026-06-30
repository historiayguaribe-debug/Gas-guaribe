from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL

# Configuración del motor
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

# ---------- FUNCIÓN get_db (necesaria para los endpoints) ----------
def get_db():
    """
    Genera una sesión de base de datos por solicitud.
    Se usa como dependencia en FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
