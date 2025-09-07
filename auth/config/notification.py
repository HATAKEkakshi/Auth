from pydantic_settings import BaseSettings, SettingsConfigDict
_base_config=SettingsConfigDict(
        env_file="./.env",  # ✅ make sure .env is in root or adjust path
        env_ignore_empty=True,
        extra="ignore"
    )
class NotificationSettings(BaseSettings):
    MAIL_USERNAME:str
    MAIL_PASSWORD:str
    MAIL_FROM:str
    MAIL_FROM_NAME:str
    MAIL_SERVER:str
    MAIL_PORT:int
    MAIL_STARTTLS:bool=True
    MAIL_SSL_TLS:bool=False
    USE_CREDENTIALS:bool=True
    VALIDATE_CERTS: bool = True
    TWILIO_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_NUMBER:str
    model_config = _base_config
class AppSettings(BaseSettings):
        APP_NAME:str="Auth"
        APP_DOMAIN:str="localhost:8006"
notification_settings = NotificationSettings()
app_settings = AppSettings()