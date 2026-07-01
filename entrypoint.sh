#!/bin/bash
set -e

echo "=== Iniciando contenedor GAS GUARIBE ==="

if [ "$RESET_DB_ON_STARTUP" = "true" ]; then
    echo "⚠️  RESET_DB_ON_STARTUP activado. Eliminando archivo de base de datos..."
    rm -f /app/gas_guaribe.db
    echo "✅ Base de datos eliminada."
fi

echo "Creando tablas en la base de datos..."
python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"
echo "✅ Tablas creadas/verificadas."

echo "Cargando datos iniciales..."
python -c "from app.database import SessionLocal; from app.cargar_datos import cargar_datos_iniciales; db=SessionLocal(); cargar_datos_iniciales(db); db.close()"
echo "✅ Datos iniciales cargados."

echo "🚀 Iniciando Uvicorn en el puerto $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
