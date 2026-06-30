FROM python:3.10-slim

WORKDIR /app

# Copiar requirements primero para aprovechar caché
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto (Render asigna el puerto dinámicamente)
EXPOSE 10000

# Comando para iniciar la aplicación (usa $PORT de Render)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
