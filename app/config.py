import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# Cambiamos el nombre de la base de datos para forzar la creación de una nueva
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gas_guaribe_nueva.db")
