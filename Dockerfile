# Usar imagen oficial de Python 3.10 slim (ligera)
FROM python:3.10-slim

# Establecer directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar requirements.txt primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar dependencias sin caché para reducir tamaño
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código fuente (app/, scripts/, templates/, static/, etc.)
COPY . .

# Copiar el script de entrada y darle permisos de ejecución
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Exponer el puerto que usará la aplicación (Render asigna uno dinámico)
EXPOSE 10000

# Usar el script de entrada como punto de inicio
ENTRYPOINT ["/entrypoint.sh"]

# El comando final se define dentro de entrypoint.sh (uvicorn)
# pero se puede dejar CMD vacío o con parámetros por defecto
CMD []
