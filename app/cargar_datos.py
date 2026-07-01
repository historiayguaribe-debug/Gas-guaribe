import logging
from sqlalchemy.orm import Session
from .models import Usuario
from .auth import get_password_hash, verify_password
from .config import settings

logger = logging.getLogger(__name__)

def cargar_datos_iniciales(db: Session):
    """
    Asegura que el usuario administrador exista y tenga la contraseña correcta.
    Si RESET_DB_ON_STARTUP es True, elimina todos los usuarios y los recrea.
    """
    # Si se pide reset, eliminar todos los usuarios (y otros datos si se desea)
    if settings.RESET_DB_ON_STARTUP:
        logger.warning("RESET_DB_ON_STARTUP activado. Eliminando todos los usuarios.")
        db.query(Usuario).delete()
        db.commit()
        logger.info("Usuarios eliminados. Se recrearán con los datos por defecto.")
        # Aquí se podrían eliminar también otras tablas si se desea un reset completo

    # 1. Asegurar que el usuario administrador existe y tiene la contraseña correcta
    admin_username = settings.ADMIN_USERNAME
    admin_password = settings.ADMIN_PASSWORD

    user = db.query(Usuario).filter(Usuario.username == admin_username).first()
    if user:
        # Si existe, verificar si la contraseña ha cambiado
        if not verify_password(admin_password, user.hashed_password):
            logger.info(f"Actualizando contraseña para usuario {admin_username}")
            user.hashed_password = get_password_hash(admin_password)
            db.commit()
            logger.info("Contraseña actualizada correctamente.")
        else:
            logger.info(f"Usuario {admin_username} ya existe con contraseña correcta.")
    else:
        # Crear nuevo usuario administrador
        logger.info(f"Creando usuario administrador {admin_username}")
        nuevo_admin = Usuario(
            username=admin_username,
            hashed_password=get_password_hash(admin_password),
            role="admin",
            nombre_completo="Administrador Principal"
        )
        db.add(nuevo_admin)
        db.commit()
        logger.info("Usuario administrador creado exitosamente.")

    # 2. Cargar otros datos iniciales (proveedores, circuitos, etc.) si no existen
    # Esta parte se mantiene igual a la que ya tiene, pero se puede mejorar con upserts.
    # Por brevedad, no la repito aquí, pero debe permanecer en su archivo.
    # Solo asegúrese de que no dependa de la existencia de usuarios para ejecutarse.
