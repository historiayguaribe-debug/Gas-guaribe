from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from .database import get_db
from .models import Circuito, Comunidad
from .auth import get_current_user, verificar_rol, oauth2_scheme
from .templates import templates

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def listar_circuitos(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    verificar_rol(user, ["admin", "operativo", "auditor"])
    circuitos = db.query(Circuito).all()
    return templates.TemplateResponse("admin_circuitos.html", {"request": request, "user": user, "circuitos": circuitos})

@router.post("/circuito/crear")
async def crear_circuito(request: Request, numero: int = Form(...), nombre: str = Form(...), descripcion: str = Form(""), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    verificar_rol(user, ["admin"])
    circuito = Circuito(numero=numero, nombre=nombre, descripcion=descripcion)
    db.add(circuito)
    db.commit()
    return RedirectResponse(url="/circuitos/", status_code=303)

@router.post("/comunidad/crear")
async def crear_comunidad(request: Request, nombre: str = Form(...), circuito_id: int = Form(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    verificar_rol(user, ["admin"])
    comunidad = Comunidad(nombre=nombre, circuito_id=circuito_id)
    db.add(comunidad)
    db.commit()
    return RedirectResponse(url="/circuitos/", status_code=303)
