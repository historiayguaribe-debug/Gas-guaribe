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

# Ejecutar el script de inicialización de la base de datos
echo "Inicializando base de datos..."
python scripts/init_db.py

echo "🚀 Iniciando Uvicorn en el puerto $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
