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

# Crear las tablas en la base de datos (si no existen)
Base.metadata.create_all(bind=engine)

# Inicializar la aplicación
app = FastAPI(title="GASGUARIBE API", version="1.0")

# Configurar CORS para permitir conexiones desde cualquier origen (útil para pruebas)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar la carpeta donde están las plantillas HTML
# Ahora busca "templates" en la raíz del contenedor (donde el Dockerfile la copió)
templates = Jinja2Templates(directory="templates")

# Incluir las rutas de los módulos (autenticación, pedidos, reportes)
app.include_router(auth_router)
app.include_router(pedidos_router)
app.include_router(reportes_router)

# --- WebSocket para seguimiento en vivo (estilo Uber) ---
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

# --- Página principal (interfaz bonita en español) ---
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- Endpoint de bienvenida (por si acaso) ---
@app.get("/api")
def api_root():
    return {"mensaje": "Bienvenido a GASGUARIBE API. Ve a /docs para probar los endpoints."}
