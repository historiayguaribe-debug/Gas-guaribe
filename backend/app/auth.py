from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from .database import get_db
from .models import Usuario, Cliente
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# --- CONFIGURACIÓN ---
router = APIRouter(prefix="/auth", tags=["Autenticación"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# --- FUNCIONES DE HASH (CON TRUNCAMIENTO PARA EVITAR ERRORES DE BCRYPT) ---
def hash_password(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt.
    IMPORTANTE: bcrypt tiene un límite de 72 bytes, por lo que truncamos la contraseña
    antes de hashearla para evitar errores como 'password cannot be longer than 72 bytes'.
    """
    # Truncar a 72 caracteres (máximo permitido por bcrypt)
    truncated_password = password[:72]
    return pwd_context.hash(truncated_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con su hash.
    También truncamos la contraseña al verificar para mantener consistencia.
    """
    truncated_password = plain_password[:72]
    return pwd_context.verify(truncated_password, hashed_password)

# --- FUNCIONES DE TOKEN JWT ---
def create_access_token(data: dict) -> str:
    """
    Crea un token JWT con expiración.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Obtiene el usuario autenticado a partir del token JWT.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# --- ENDPOINTS PÚBLICOS ---

@router.post("/registro")
def registro(
    email: str,
    password: str,
    nombre: str,
    telefono: str,
    rol: str,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo usuario en el sistema.
    - email: correo electrónico (debe ser único)
    - password: contraseña (será hasheada automáticamente)
    - nombre: nombre completo
    - telefono: número de contacto
    - rol: cliente, repartidor o admin
    """
    # Verificar si el email ya existe
    existe = db.query(Usuario).filter(Usuario.email == email).first()
    if existe:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Crear el nuevo usuario
    nuevo_usuario = Usuario(
        email=email,
        hashed_password=hash_password(password),
        nombre=nombre,
        telefono=telefono,
        rol=rol
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    # Si es cliente, crear su perfil básico
    if rol == "cliente":
        nuevo_cliente = Cliente(
            usuario_id=nuevo_usuario.id,
            direccion="Dirección pendiente de actualizar",
            lat=10.0,  # Coordenadas genéricas (el usuario las actualizará luego)
            lng=-66.0,
            es_institucion=False,
            exonerado=False
        )
        db.add(nuevo_cliente)
        db.commit()
    
    return {
        "mensaje": "Usuario creado exitosamente",
        "usuario_id": nuevo_usuario.id,
        "email": nuevo_usuario.email,
        "rol": nuevo_usuario.rol
    }

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Inicia sesión y devuelve un token JWT.
    Usa OAuth2 (form-data) con campos username y password.
    """
    usuario = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    
    # Verificar credenciales
    if not usuario or not verify_password(form_data.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token de acceso
    token = create_access_token(data={"sub": usuario.email, "rol": usuario.rol})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "rol": usuario.rol,
        "usuario_id": usuario.id,
        "nombre": usuario.nombre
    }

@router.get("/me")
def get_me(current_user: Usuario = Depends(get_current_user)):
    """
    Devuelve la información del usuario autenticado.
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "nombre": current_user.nombre,
        "telefono": current_user.telefono,
        "rol": current_user.rol,
        "fecha_registro": current_user.fecha_registro
    }
