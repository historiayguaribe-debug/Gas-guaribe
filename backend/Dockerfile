FROM python:3.10-slim

WORKDIR /app

# Copiar requirements.txt desde la carpeta backend
COPY backend/requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el contenido de backend/app
COPY backend/app ./app

# Copiar la carpeta templates
COPY backend/templates ./templates

# Comando para iniciar el servidor (CORREGIDO)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
