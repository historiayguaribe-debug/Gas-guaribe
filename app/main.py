from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .database import engine, SessionLocal
from .models import Base
from .auth import authenticate_user, create_access_token, get_current_user, get_db, oauth2_scheme
from .cargar_datos import cargar_datos_iniciales
from .config import settings
from datetime import timedelta
from . import admin_routes, cargas_routes, ventas_routes, clientes_routes, circuitos_routes, pedidos_routes, reportes_routes, asistente_routes
from .templates import templates
from datetime import datetime

Base.metadata.create_all(bind=engine)

app = FastAPI(title="GAS GUARIBE")
app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    if user.role == "cliente":
        return RedirectResponse(url="/pedidos/cliente/dashboard")
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

@app.get("/logout")
async def logout():
    return RedirectResponse(url="/login")
