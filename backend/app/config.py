from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AutoBiz Engine"
    DEBUG: bool = False
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://autobiz:secret@localhost:5432/autobiz_engine"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_POOL_TIMEOUT: int = 30

    # LLM Provider — uses OpenAI-compatible API (OpenRouter, local, etc.)
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4-turbo"
    LLM_BASE_URL: str = ""
    LLM_TEMPERATURE: float = 0.7

    # Embedding Provider
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_BASE_URL: str = ""

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Legacy — kept for backward compatibility
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo"
    ANTHROPIC_API_KEY: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    CELERY_TASK_TIME_LIMIT: int = 3600
    CELERY_TASK_SOFT_TIME_LIMIT: int = 1800

    # Notifications (user configures via TUI)
    RESEND_API_KEY: str = ""
    SENDGRID_API_KEY: str = ""

    # Monitoring
    SENTRY_DSN: str = ""
    DISCORD_WEBHOOK_URL: str = ""

    # Environment
    ENVIRONMENT: str = "development"

    # Feature Flags
    ENABLE_AUTO_APPROVE: bool = False
    MAX_BUDGET_PER_BUSINESS: float = 5000.0

    @model_validator(mode="after")
    def _validate_required(self):
        if not self.SECRET_KEY:
            raise ValueError(
                "SECRET_KEY is required. Run ./autobiz or set it in .env:\n"
                "  SECRET_KEY=$(openssl rand -hex 32)"
            )
        if "secret" in self.DATABASE_URL and "localhost" not in self.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL contains default password 'secret'. "
                "Set a real password in .env:\n"
                "  DATABASE_URL=postgresql+psycopg2://user:realpass@host:5432/db"
            )
        return self

    class Config:
        env_file = ".env", "../.env", "../../.env"
        case_sensitive = False


settings = Settings()
