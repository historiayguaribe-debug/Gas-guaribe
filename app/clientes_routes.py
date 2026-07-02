from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from .database import get_db
from .models import Cliente, Comunidad
from .auth import get_current_user, verificar_rol, oauth2_scheme
from .templates import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def listar_clientes(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    verificar_rol(user, ["admin", "operativo", "auditor"])
    clientes = db.query(Cliente).all()
    comunidades = db.query(Comunidad).all()
    return templates.TemplateResponse("admin_clientes.html", {"request": request, "user": user, "clientes": clientes, "comunidades": comunidades})

@router.post("/crear")
async def crear_cliente(request: Request, nombre: str = Form(...), cedula_rif: str = Form(...), telefono: str = Form(...), direccion: str = Form(...), comunidad_id: int = Form(...), tipo: str = Form("Normal"), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    verificar_rol(user, ["admin", "operativo"])
    cliente = Cliente(nombre=nombre, cedula_rif=cedula_rif, telefono=telefono, direccion=direccion, comunidad_id=comunidad_id, tipo=tipo)
    db.add(cliente)
    db.commit()
    return RedirectResponse(url="/clientes/", status_code=303)
