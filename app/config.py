"""
Configuration settings for Immobili Images API.
"""
from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """Application settings."""

    # Database (read-only)
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 168  # 7 giorni

    # API User
    API_USERNAME: str
    API_PASSWORD: str

    # Application
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    CORS_ORIGINS: str = '["*"]'

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8002

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

    @property
    def database_url(self) -> str:
        """PostgreSQL database URL (read-only)."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string."""
        try:
            return json.loads(self.CORS_ORIGINS)
        except:
            return ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
