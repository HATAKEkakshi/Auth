from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings, SettingsConfigDict
_base_config=SettingsConfigDict(
        env_file="./.env",  # ✅ make sure .env is in root or adjust path
        env_ignore_empty=True,
        extra="ignore"
    )
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.auth
user1_collection_name=db["User1"]
user2_collection_name=db["User2"]
class DatabaseSettings(BaseSettings):
    REDIS_HOST: str
    REDIS_PORT: str

    model_config = _base_config

db_settings = DatabaseSettings()


