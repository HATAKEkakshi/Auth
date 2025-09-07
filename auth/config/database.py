from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings, SettingsConfigDict
from auth.logger.log import logger
import asyncio
# Configuration for loading environment variables
_base_config=SettingsConfigDict(
        env_file="./.env",  # Load environment variables from .env file
        env_ignore_empty=True,
        extra="ignore"
    )

# MongoDB connection setup
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.auth  # Auth database
user1_collection_name=db["User1"]  # User1 collection for multi-user support
user2_collection_name=db["User2"]  # User2 collection for multi-user support
class DatabaseSettings(BaseSettings):
    REDIS_HOST: str
    REDIS_PORT: str
    def REDIS_URL(self, db) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{db}"
    model_config = _base_config
"""Check MongoDB connection health status"""
async def check_database_health():
    try:
        await client.admin.command('ping')
        logger("Auth", "Database", "INFO", "null", "Database connection successful")
        return True
    except Exception as e:
        logger("Auth", "Database", "ERROR", "CRITICAL", f"Database connection failed: {str(e)}")
        return False

"""Continuously monitor database health every 60 seconds"""
async def monitor_database():
    while True:
        await check_database_health()
        await asyncio.sleep(60)  # Check every 60 seconds

"""Initialize database health monitoring as background task"""
def start_db_monitoring():
    asyncio.create_task(monitor_database())

# Load database settings from environment variables
db_settings = DatabaseSettings()