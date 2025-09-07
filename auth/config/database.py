from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings, SettingsConfigDict
from auth.logger.log import logger
import asyncio
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
"""
Database connection and monitoring setup.
Monitors the health of the MongoDB connection.

"""
async def check_database_health():
    try:
        await client.admin.command('ping')
        logger("Auth", "Database", "info", "null", "Database connection successful")
        return True
    except Exception as e:
        logger("Auth", "Database", "error", "CRITICAL", f"Database connection failed: {str(e)}")
        return False

async def monitor_database():
    while True:
        await check_database_health()
        await asyncio.sleep(60)  # Check every 60 seconds

def start_db_monitoring():
    asyncio.create_task(monitor_database())

db_settings = DatabaseSettings()