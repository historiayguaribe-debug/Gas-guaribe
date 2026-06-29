FROM python:3.10-slim

WORKDIR /app

# Copiar requirements.txt desde la carpeta backend
COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar el contenido de backend/app
COPY backend/app ./app

# Copiar la carpeta templates (¡esta es la línea que faltaba!)
COPY backend/templates ./templates

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
