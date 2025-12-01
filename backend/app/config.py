"""
Application configuration
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # API Keys
    openai_api_key: str

    # Database
    database_url: str = "postgresql://localhost:5432/resume_agent"

    # Application
    app_name: str = "Resume Agent"
    debug: bool = False

    # CORS
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


