#!/bin/bash
set -e

echo "=== Iniciando contenedor GAS GUARIBE ==="
echo "DATABASE_URL (entorno) = ${DATABASE_URL:-no definida}"

if [ -z "$DATABASE_URL" ] || [ "$DATABASE_URL" = "''" ]; then
    echo "⚠️  DATABASE_URL está vacía. Usando valor por defecto."
    export DATABASE_URL="sqlite:///./gas_guaribe.db"
fi

echo "DATABASE_URL (final) = $DATABASE_URL"

if [ "$RESET_DB_ON_STARTUP" = "true" ]; then
    echo "⚠️  RESET_DB_ON_STARTUP activado. Eliminando archivo de base de datos..."
    rm -f /app/gas_guaribe.db
    echo "✅ Base de datos eliminada."
fi

echo "Creando tablas en la base de datos..."
python -c "
from app.database import engine, Base
# Importar explícitamente los modelos para registrarlos
from app.models import Usuario, Proveedor, Circuito, Comunidad, Cliente, Cilindro, Carga, Venta, GastoOperativo, Pedido
Base.metadata.create_all(bind=engine)
print('✅ Tablas creadas/verificadas.')
"

echo "Cargando datos iniciales..."
python -c "from app.database import SessionLocal; from app.cargar_datos import cargar_datos_iniciales; db=SessionLocal(); cargar_datos_iniciales(db); db.close()"
echo "✅ Datos iniciales cargados."

echo "🚀 Iniciando Uvicorn en el puerto $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
