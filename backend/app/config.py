from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AutoBiz Engine"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-for-hashing"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://yourdomain.com",
    ]

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/autobiz_engine"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_POOL_TIMEOUT: int = 30

    # OpenAI
    OPENAI_API_KEY: str = "your-openai-api-key"
    OPENAI_MODEL: str = "gpt-4-turbo"

    # Anthropic
    ANTHROPIC_API_KEY: str = "your-anthropic-api-key"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    CELERY_TASK_TIME_LIMIT: int = 3600
    CELERY_TASK_SOFT_TIME_LIMIT: int = 1800

    # Stripe
    STRIPE_API_KEY: str = "your-stripe-api-key"
    STRIPE_WEBHOOK_SECRET: str = "your-stripe-webhook-secret"
    STRIPE_STARTER_PRICE_ID: str = "price_starter_monthly"
    STRIPE_GROWTH_PRICE_ID: str = "price_growth_monthly"
    STRIPE_ENTERPRISE_PRICE_ID: str = "price_enterprise_monthly"

    # Email
    RESEND_API_KEY: str = "your-resend-api-key"
    SENDGRID_API_KEY: str = "your-sendgrid-api-key"

    # Supabase
    SUPABASE_URL: str = "https://your-project.supabase.co"
    SUPABASE_KEY: str = "your-supabase-key"

    # AWS
    AWS_ACCESS_KEY_ID: str = "your-aws-access-key"
    AWS_SECRET_ACCESS_KEY: str = "your-aws-secret-key"
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = "autobiz-engine-storage"

    # Monitoring
    SENTRY_DSN: str = ""
    DISCORD_WEBHOOK_URL: str = ""

    # Feature Flags
    ENABLE_AUTO_APPROVE: bool = False
    MAX_BUDGET_PER_BUSINESS: float = 5000.0

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
