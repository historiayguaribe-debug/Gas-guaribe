import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./gas_guaribe.db")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "gas.guaribe")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "gas2026")
    RESET_DB_ON_STARTUP: bool = os.getenv("RESET_DB_ON_STARTUP", "false").lower() == "true"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 día

settings = Settings()
