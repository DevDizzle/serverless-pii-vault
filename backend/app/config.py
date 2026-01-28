from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_ID: str = "profitscout-lx6bb"
    QUARANTINE_BUCKET: str = "profitscout-lx6bb-quarantine"
    VAULT_BUCKET: str = "profitscout-lx6bb-vault"
    REGION: str = "us-central1"
    DATABASE_URL: str = "postgresql://user:password@localhost/dbname"
    
    # Flags for local dev to mock GCP services
    USE_MOCK_GCP: bool = False
    
    SERVICE_ACCOUNT_EMAIL: str = "mock-sa@example.com"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
