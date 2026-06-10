from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import ConfigDict, computed_field


class Settings(BaseSettings):
    firebase_project_id: str = "your-firebase-project-id"
    firebase_api_key: str = "your-firebase-api-key"
    firebase_auth_domain: Optional[str] = None
    firebase_storage_bucket: Optional[str] = None
    firebase_messaging_sender_id: Optional[str] = None
    firebase_app_id: Optional[str] = None
    firebase_measurement_id: Optional[str] = None
    # Provide Firebase service account credentials as a JSON string (useful when storing credentials in Secrets).
    # Example env var: FIREBASE_CREDENTIALS_JSON='{"type": "service_account", ... }'
    firebase_credentials_json: Optional[str] = None
    secret_key: str
    access_token_expire_minutes: int = 1440
    refresh_token_expire_minutes: int = 43200
    admin_phone: str
    admin_name: str
    admin_surname: str
    
    # Twilio Configuration
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_verify_service_sid: Optional[str] = None
    
    environment: str = "development"
    log_level: str = "INFO"

    model_config = ConfigDict(env_file=".env", extra="ignore")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_firebase_storage_bucket(self) -> Optional[str]:
        if self.firebase_storage_bucket:
            return self.firebase_storage_bucket
        if self.firebase_project_id and self.firebase_project_id != "your-firebase-project-id":
            return f"{self.firebase_project_id}.firebasestorage.app"
        return None


settings = Settings()
