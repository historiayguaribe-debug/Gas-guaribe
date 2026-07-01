import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# ⚠️ CAMBIAMOS EL NOMBRE DE LA BASE DE DATOS PARA FORZAR RECREACIÓN
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gas_guaribe_nueva.db")
