from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_ID: str = "mock-project-id"
    QUARANTINE_BUCKET: str = "mock-quarantine-bucket"
    VAULT_BUCKET: str = "mock-vault-bucket"
    REGION: str = "us-central1"
    DATABASE_URL: str = "postgresql://user:password@localhost/dbname"
    
    # Flags for local dev to mock GCP services
    USE_MOCK_GCP: bool = False

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
