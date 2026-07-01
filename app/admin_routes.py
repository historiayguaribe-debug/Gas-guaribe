from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from .database import get_db
from .models import Usuario
from .auth import get_current_user, verificar_rol, get_password_hash, oauth2_scheme
from .templates import templates

router = APIRouter()

@router.get("/usuarios", response_class=HTMLResponse)
async def listar_usuarios(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    verificar_rol(user, ["admin"])
    usuarios = db.query(Usuario).all()
    return templates.TemplateResponse("admin_usuarios.html", {"request": request, "user": user, "usuarios": usuarios})

@router.post("/usuarios/crear")
async def crear_usuario(request: Request, username: str = Form(...), password: str = Form(...), role: str = Form(...), nombre: str = Form(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    verificar_rol(user, ["admin"])
    hashed = get_password_hash(password)
    nuevo = Usuario(username=username, hashed_password=hashed, role=role, nombre_completo=nombre)
    db.add(nuevo)
    db.commit()
    return RedirectResponse(url="/admin/usuarios", status_code=303)
