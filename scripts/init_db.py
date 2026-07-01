# scripts/init_db.py
import sys
import os

# Agregar el directorio raíz al path para poder importar app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app.models import Usuario, Proveedor, Circuito, Comunidad, Cliente, Cilindro, Carga, Venta, GastoOperativo, Pedido
from app.cargar_datos import cargar_datos_iniciales
from app.database import SessionLocal

def main():
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas/verificadas.")
    
    print("Cargando datos iniciales...")
    db = SessionLocal()
    cargar_datos_iniciales(db)
    db.close()
    print("✅ Datos iniciales cargados.")

if __name__ == "__main__":
    main()
