from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from .database import engine, Base
from .auth import router as auth_router
from .pedidos import router as pedidos_router
from .reportes import router as reportes_router
from .websocket_manager import manager
from .asistente import generar_respuesta
from .cargar_datos import cargar_datos
from .admin_routes import router as admin_router
from pydantic import BaseModel
import json

class Pregunta(BaseModel):
    pregunta: str

Base.metadata.create_all(bind=engine)

app = FastAPI(title="GASGUARIBE API", version="2.0")

# Cargar datos de prueba (solo si la base está vacía)
try:
    cargar_datos()
except Exception as e:
    print(f"⚠️ Error al cargar datos: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

app.include_router(auth_router)
app.include_router(pedidos_router)
app.include_router(reportes_router)
app.include_router(admin_router)  # <--- Nueva ruta para el panel

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            json_data = json.loads(data)
            if json_data.get("type") == "location":
                await websocket.send_text(json.dumps({"status": "ubicacion_recibida"}))
    except WebSocketDisconnect:
        manager.disconnect(user_id)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api")
def api_root():
    return {"mensaje": "Bienvenido a GASGUARIBE API", "documentacion": "/docs", "panel": "/admin/panel"}

@app.post("/asistente/preguntar")
async def preguntar_asistente(pregunta: Pregunta):
    respuesta = generar_respuesta(pregunta.pregunta)
    return {"respuesta": respuesta}

@app.get("/admin", response_class=HTMLResponse)
async def admin_chat(request: Request):
    return templates.TemplateResponse("admin_chat.html", {"request": request})

@app.get("/status")
def status():
    return {"estado": "online", "version": "2.0"}
