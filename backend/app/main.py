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
from pydantic import BaseModel
import json

# --- MODELO PARA LAS PREGUNTAS DEL ASISTENTE ---
class Pregunta(BaseModel):
    pregunta: str

# --- CREAR LAS TABLAS EN LA BASE DE DATOS ---
Base.metadata.create_all(bind=engine)

# --- INICIALIZAR LA APLICACIÓN ---
app = FastAPI(title="GASGUARIBE API", version="1.0")

# --- CONFIGURAR CORS (para permitir peticiones desde el móvil o navegador) ---
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
                # Aquí iría la lógica para notificar al cliente
                await websocket.send_text(json.dumps({"status": "ubicacion_recibida"}))
    except WebSocketDisconnect:
        manager.disconnect(user_id)

# --- PÁGINA PRINCIPAL (interfaz bonita en español) ---
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- ENDPOINT DE BIENVENIDA (para probar que la API funciona) ---
@app.get("/api")
def api_root():
    return {"mensaje": "Bienvenido a GASGUARIBE API. Ve a /docs para probar los endpoints."}

# --- NUEVO: ASISTENTE INTELIGENTE (CHAT CON GROQ) ---
@app.post("/asistente/preguntar")
async def preguntar_asistente(pregunta: Pregunta):
    """
    Endpoint que recibe una pregunta del usuario, consulta a Groq y devuelve la respuesta.
    """
    respuesta = generar_respuesta(pregunta.pregunta)
    return {"respuesta": respuesta}

# --- NUEVO: PÁGINA DE CHAT DEL ADMINISTRADOR ---
@app.get("/admin", response_class=HTMLResponse)
async def admin_chat(request: Request):
    """
    Página con la interfaz de chat para que el administrador hable con el asistente IA.
    """
    return templates.TemplateResponse("admin_chat.html", {"request": request})
