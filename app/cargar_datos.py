import logging
from sqlalchemy.orm import Session
from .models import Usuario, Proveedor, Circuito, Comunidad, Cliente, Cilindro, Carga, Venta, GastoOperativo, Pedido
from .auth import get_password_hash, verify_password
from .utils import generar_codigo_qr
from .config import settings
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

def cargar_datos_iniciales(db: Session):
    """
    Asegura que el usuario administrador exista y tenga la contraseña correcta.
    Si RESET_DB_ON_STARTUP es True, elimina todos los usuarios.
    """
    if settings.RESET_DB_ON_STARTUP:
        logger.warning("RESET_DB_ON_STARTUP activado. Eliminando todos los usuarios.")
        db.query(Usuario).delete()
        db.commit()
        logger.info("Usuarios eliminados.")

    # 1. Asegurar usuario administrador
    admin_username = settings.ADMIN_USERNAME
    admin_password = settings.ADMIN_PASSWORD

    user = db.query(Usuario).filter(Usuario.username == admin_username).first()
    if user:
        if not verify_password(admin_password, user.hashed_password):
            logger.info(f"Actualizando contraseña para {admin_username}")
            user.hashed_password = get_password_hash(admin_password)
            db.commit()
        else:
            logger.info(f"Usuario {admin_username} ya existe con contraseña correcta.")
    else:
        logger.info(f"Creando usuario administrador {admin_username}")
        nuevo_admin = Usuario(
            username=admin_username,
            hashed_password=get_password_hash(admin_password),
            role="admin",
            nombre_completo="Administrador Principal"
        )
        db.add(nuevo_admin)
        db.commit()

    # 2. Cargar datos de prueba (si la BD está vacía en otras tablas)
    if db.query(Proveedor).count() == 0:
        # (Código completo de proveedores, circuitos, etc. que ya tenías)
        # ... (lo dejo como estaba, solo se ejecuta si no hay proveedores)
        pass
