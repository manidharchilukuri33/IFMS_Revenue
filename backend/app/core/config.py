import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

_env_file = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=_env_file if _env_file.exists() else None)

class Settings(BaseSettings):
    PROJECT_NAME: str = "IFMS Revenue Collection & Reconciliation Module"
    API_V1_STR: str = "/api/v1"
    
    # Database Settings
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "ifms_budget")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "ifms_budget")
    DB_NAME: str = os.getenv("DB_NAME", "ifms_budget")
    DB_SCHEMA: str = "ifms_budget"
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Default Business Date & Financial Year
    DEFAULT_BUSINESS_DATE: str = "2026-09-15"
    DEFAULT_FINANCIAL_YEAR: str = "2026-27"
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

settings = Settings()
