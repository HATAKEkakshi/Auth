from redis.asyncio import Redis
from typing import Optional, Dict, Any
import json
import asyncio
from auth.config.database import db_settings
from auth.logger.log import logger
"""Create Redis client connection"""
async def get_redis_client():
    return Redis(
        host=db_settings.REDIS_HOST,
        port=db_settings.REDIS_PORT,
        db=0,
        decode_responses=True
    )

"""Set data in Redis cache with expiration time"""
async def set_profile_data(key: str, ttl: int, profile_data: dict):
    redis_client = await get_redis_client()
    try:
        json_data = json.dumps(profile_data)
        await redis_client.setex(key, ttl, json_data)
        logger("Auth", "Redis Cache", "INFO", "null", f"Setting data for key in cache: {key} with TTL: {ttl}")
    except Exception as e:
        logger("Auth", "Redis Cache", "ERROR", "HIGH", f"Redis error: {e}")
    finally:
        await redis_client.close()

"""Get data from Redis cache by key"""
async def get_profile_data(key: str) -> Optional[dict]:
    redis_client = await get_redis_client()
    try:
        json_data = await redis_client.get(key)
        if json_data:
            logger("Auth", "Redis Cache", "INFO", "null", f"Cache hit getting data for key from cache: {key}")
            return json.loads(json_data)
        logger("Auth", "Redis Cache", "WARN", "LOW", f"Cache miss for key: {key}")
        return None
    except Exception as e:
        logger("Auth", "Redis Cache", "ERROR", "ERROR", f"Redis error: {e}")
        return None
    finally:
        await redis_client.close()

"""Delete data from Redis cache by key"""
async def delete_profile_data(key: str):
    redis_client = await get_redis_client()
    try:
        await redis_client.delete(key)
        logger("Auth", "Redis Cache", "INFO", "null", f"Deleted data for key in cache: {key}")
    except Exception as e:
        logger("Auth", "Redis Cache", "ERROR", "ERROR", f"Redis error: {e}")
    finally:
        await redis_client.close()

"""Add JWT token to blacklist for logout security"""
async def add_jti_to_blacklist(jti: str):
    redis_client = await get_redis_client()
    try:
        await redis_client.set(jti, "blacklisted")
        logger("Auth", "Redis Cache", "INFO", "null", f"Added JTI to blacklist: {jti}")
    except Exception as e:
        logger("Auth", "Redis Cache", "ERROR", "ERROR", f"Redis error: {e}")
    finally:
        await redis_client.close()

"""Check if JWT token is blacklisted"""
async def is_jti_blacklisted(jti: str) -> bool:
    redis_client = await get_redis_client()
    try:
        exists = await redis_client.exists(jti)
        logger("Auth", "Redis Cache", "INFO", "null", f"Checked JTI in blacklist: {jti}, Exists: {exists}")
        return exists == 1
    except Exception as e:
        logger("Auth", "Redis Cache", "ERROR", "ERROR", f"Redis error: {e}")
        return False
    finally:
        await redis_client.close()

"""Check Redis connection health status"""
async def check_redis_health():
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        logger("Auth", "Redis Cache", "INFO", "null", "Redis connection successful")
        return True
    except Exception as e:
        logger("Auth", "Redis Cache", "ERROR", "CRITICAL", f"Redis connection failed: {str(e)}")
        return False
"""Continuously monitor Redis health every 60 seconds"""
async def monitor_redis():
    while True:
        await check_redis_health()
        await asyncio.sleep(60)
"""Initialize Redis health monitoring as background task"""
def start_redis_monitoring():
    asyncio.create_task(monitor_redis())