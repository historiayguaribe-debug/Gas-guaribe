import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Usuario
from .config import settings

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    logger.info(f"Intentando autenticar usuario: {username}")
    user = db.query(Usuario).filter(Usuario.username == username).first()
    if not user:
        logger.warning(f"Usuario {username} no encontrado en la base de datos.")
        return False
    logger.info(f"Usuario {username} encontrado. Verificando contraseña...")
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Contraseña incorrecta para usuario {username}")
        return False
    logger.info(f"Autenticación exitosa para {username}")
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Token sin 'sub'")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"Error al decodificar token: {e}")
        raise credentials_exception
    db = SessionLocal()
    user = db.query(Usuario).filter(Usuario.username == username).first()
    db.close()
    if user is None:
        logger.warning(f"Usuario {username} no encontrado en BD para el token")
        raise credentials_exception
    return user

def verificar_rol(user, roles_permitidos: list):
    if user.role not in roles_permitidos:
        raise HTTPException(status_code=403, detail="No autorizado")
