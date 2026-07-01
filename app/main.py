from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .database import engine, SessionLocal
from .models import Base, Usuario
from .cargar_datos import cargar_datos_iniciales
from .templates import templates
from datetime import datetime
from . import admin_routes, cargas_routes, ventas_routes, clientes_routes, circuitos_routes, pedidos_routes, reportes_routes, asistente_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="GAS GUARIBE - Acceso Directo")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Incluir routers
app.include_router(admin_routes.router, prefix="/admin", tags=["admin"])
app.include_router(cargas_routes.router, prefix="/cargas", tags=["cargas"])
app.include_router(ventas_routes.router, prefix="/ventas", tags=["ventas"])
app.include_router(clientes_routes.router, prefix="/clientes", tags=["clientes"])
app.include_router(circuitos_routes.router, prefix="/circuitos", tags=["circuitos"])
app.include_router(pedidos_routes.router, prefix="/pedidos", tags=["pedidos"])
app.include_router(reportes_routes.router, prefix="/reportes", tags=["reportes"])
app.include_router(asistente_routes.router, prefix="/asistente", tags=["asistente"])

@app.on_event("startup")
def startup():
    db = SessionLocal()
    cargar_datos_iniciales(db)
    db.close()

# Redirige la raíz directamente al dashboard
@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/dashboard")

# El login ahora solo redirige al dashboard sin pedir credenciales
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return RedirectResponse(url="/dashboard")

# Dashboard con acceso directo (sin autenticación)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(SessionLocal)):
    # Crear un usuario fijo en memoria para mostrar en el menú
    user = Usuario(
        username="gas.guaribe",
        role="admin",
        nombre_completo="Administrador (Acceso Directo)"
    )
    # Estadísticas
    from .models import Cilindro, Venta
    disponibles = db.query(Cilindro).filter(Cilindro.estado == "disponible").count()
    ventas_hoy = db.query(Venta).filter(Venta.fecha >= datetime.utcnow().date()).all()
    ingresos_hoy = sum(v.cantidad * v.precio_unitario for v in ventas_hoy)
    exonerados_hoy = sum(1 for v in ventas_hoy if v.exonerado)
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "user": user,
        "disponibles": disponibles,
        "ventas_hoy": len(ventas_hoy),
        "ingresos_hoy": ingresos_hoy,
        "exonerados_hoy": exonerados_hoy
    })

# Cerrar sesión simplemente redirige al dashboard
@app.get("/logout")
async def logout():
    return RedirectResponse(url="/dashboard")
