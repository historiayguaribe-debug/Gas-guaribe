import os

SECRET_KEY = os.environ.get("SECRET_KEY", "mi_clave_super_secreta_para_guaribe_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./gasguaribe.db")
