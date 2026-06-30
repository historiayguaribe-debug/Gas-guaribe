from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL

# Crear el motor de la base de datos
# Si es SQLite, se añade "check_same_thread=False" para permitir múltiples hilos
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para los modelos (declarative_base)
Base = declarative_base()

# ---------- FUNCIÓN get_db (necesaria para los endpoints) ----------
def get_db():
    """
    Genera una sesión de base de datos por solicitud.
    Se usa como dependencia en FastAPI para inyectar la sesión en los endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
