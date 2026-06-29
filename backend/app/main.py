from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from .database import engine, Base
from .auth import router as auth_router
from .pedidos import router as pedidos_router
from .reportes import router as reportes_router
from .websocket_manager import manager
import json
import os

# Crear las tablas en la base de datos (si no existen)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="GASGUARIBE API", version="1.0")

# Configurar CORS para permitir conexiones desde el móvil o navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar la carpeta donde están las plantillas HTML
templates = Jinja2Templates(directory="app/templates")

# Incluir las rutas de los módulos
app.include_router(auth_router)
app.include_router(pedidos_router)
app.include_router(reportes_router)

# --- WebSocket para seguimiento en vivo ---
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            json_data = json.loads(data)
            if json_data.get("type") == "location":
                lat = json_data.get("lat")
                lng = json_data.get("lng")
                await websocket.send_text(json.dumps({"status": "ubicacion_recibida"}))
    except WebSocketDisconnect:
        manager.disconnect(user_id)

# --- PÁGINA PRINCIPAL BONITA EN ESPAÑOL ---
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})ra probar los endpoints."}
