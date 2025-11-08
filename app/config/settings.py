from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import ConfigDict


class Settings(BaseSettings):
    firebase_project_id: str = "your-firebase-project-id"
    firebase_api_key: str = "your-firebase-api-key"
    firebase_credentials_path: Optional[str] = None
    secret_key: str
    access_token_expire_minutes: int = 1440
    admin_phone: str
    admin_name: str
    admin_surname: str
    environment: str = "development"
    log_level: str = "INFO"

    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()
