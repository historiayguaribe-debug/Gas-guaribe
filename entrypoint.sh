#!/bin/bash
set -e

echo "=== Iniciando contenedor GAS GUARIBE ==="

# Si se pide reset, eliminar la base de datos
if [ "$RESET_DB_ON_STARTUP" = "true" ]; then
    echo "⚠️  RESET_DB_ON_STARTUP activado. Eliminando archivo de base de datos..."
    rm -f /app/gas_guaribe.db
    echo "✅ Base de datos eliminada."
fi

# Crear tablas (si no existen)
echo "Creando tablas en la base de datos..."
python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"
echo "✅ Tablas creadas/verificadas."

# Cargar datos iniciales (crea/actualiza usuario admin y otros datos)
echo "Cargando datos iniciales..."
python -c "from app.database import SessionLocal; from app.cargar_datos import cargar_datos_iniciales; db=SessionLocal(); cargar_datos_iniciales(db); db.close()"
echo "✅ Datos iniciales cargados."

# Iniciar la aplicación
echo "🚀 Iniciando Uvicorn en el puerto $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
