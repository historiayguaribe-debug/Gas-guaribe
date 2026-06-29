import os

# Clave secreta para tokens (cámbiala en producción)
SECRET_KEY = "mi_clave_super_secreta_para_guaribe_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 día

# Base de datos SQLite (se creará sola)
DATABASE_URL = "sqlite:///./gasguaribe.db"
