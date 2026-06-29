from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .auth import router as auth_router
from .pedidos import router as pedidos_router
from .reportes import router as reportes_router
from .websocket_manager import manager
import json

Base.metadata.create_all(bind=engine)

app = FastAPI(title="GASGUARIBE API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(pedidos_router)
app.include_router(reportes_router)

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

@app.get("/")
def root():
    return {"mensaje": "Bienvenido a GASGUARIBE API. Ve a /docs para probar los endpoints."}
