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

# --- MODELO PARA LAS PREGUNTAS DEL ASISTENTE ---
class Pregunta(BaseModel):
    pregunta: str

# --- CREAR LAS TABLAS EN LA BASE DE DATOS ---
Base.metadata.create_all(bind=engine)

# --- INICIALIZAR LA APLICACIÓN ---
app = FastAPI(
    title="GASGUARIBE API",
    version="2.0",
    description="Sistema de gestión y reparto de gas doméstico con asistente IA y panel de administración"
)

# --- CARGAR DATOS DE PRUEBA AUTOMÁTICAMENTE ---
try:
    cargar_datos()
except Exception as e:
    print(f"⚠️ No se pudieron cargar los datos de prueba: {e}")

# --- CONFIGURAR CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURAR LA CARPETA DE PLANTILLAS HTML ---
templates = Jinja2Templates(directory="templates")

# --- INCLUIR LAS RUTAS DE LOS MÓDULOS ---
app.include_router(auth_router)
app.include_router(pedidos_router)
app.include_router(reportes_router)
app.include_router(admin_router)

# --- WEB SOCKET PARA SEGUIMIENTO EN VIVO ---
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

# --- PÁGINA PRINCIPAL ---
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- PÁGINA DE LOGIN (NUEVA) ---
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# --- ENDPOINT DE BIENVENIDA ---
@app.get("/api")
def api_root():
    return {
        "mensaje": "Bienvenido a GASGUARIBE API",
        "documentacion": "/docs",
        "login": "/login",
        "panel_administracion": "/admin/panel",
        "version": "2.0"
    }

# --- ASISTENTE INTELIGENTE ---
@app.post("/asistente/preguntar")
async def preguntar_asistente(pregunta: Pregunta):
    respuesta = generar_respuesta(pregunta.pregunta)
    return {"respuesta": respuesta}

# --- PÁGINA DE CHAT DEL ADMINISTRADOR ---
@app.get("/admin", response_class=HTMLResponse)
async def admin_chat(request: Request):
    return templates.TemplateResponse("admin_chat.html", {"request": request})

# --- ENDPOINT DE ESTADO DEL SISTEMA ---
@app.get("/status")
def status():
    return {
        "estado": "online",
        "servicio": "GASGUARIBE",
        "version": "2.0",
        "base_datos": "SQLite",
        "panel_admin": "/admin/panel",
        "login": "/login"
    }
