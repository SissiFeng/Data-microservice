import os
from pydantic_settings import BaseSettings # Changed import from pydantic to pydantic_settings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Data Processing Microservice"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # AWS S3 settings
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "data-microservice-bucket")
    
    # Data directory settings
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    WATCH_DIR: str = os.getenv("WATCH_DIR", "watch")
    
    # Database settings
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "app")
    
    # Special override for Alembic generation if no real DB is available
    ALEMBIC_GENERATE_OFFLINE: bool = os.getenv("ALEMBIC_GENERATE_OFFLINE", "false").lower() == "true"

    if ALEMBIC_GENERATE_OFFLINE:
        DATABASE_URL: str = "sqlite+aiosqlite:///./alembic_dummy_for_generation.db"
    else:
        DATABASE_URL: str = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # Celery settings
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
    
    class Config:
        case_sensitive = True

settings = Settings()
