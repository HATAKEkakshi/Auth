from redis.asyncio import Redis
from typing import Optional, Dict, Any
import json
import asyncio
from auth.config.database import db_settings
from auth.logger.log import logger
from auth.config.bloom import bloom_service
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

"""Add JWT token to blacklist with Bloom filter optimization"""
async def add_jti_to_blacklist(jti: str):
    redis_client = await get_redis_client()
    try:
        # Add to both Bloom filter and Redis
        bloom_service.add_blacklisted_token(jti)
        await redis_client.set(jti, "blacklisted")
        logger("Auth", "Redis Cache", "INFO", "null", f"Token blacklisted with Bloom filter: {jti[:10]}...")
    except Exception as e:
        logger("Auth", "Redis Cache", "ERROR", "ERROR", f"Failed to blacklist token: {str(e)}")
        raise
    finally:
        await redis_client.close()

"""Check if JWT token is blacklisted using Bloom filter first"""
async def is_jti_blacklisted(jti: str) -> bool:
    try:
        # Fast Bloom filter check first
        if not bloom_service.is_token_blacklisted(jti):
            # Definitely not blacklisted
            return False
        
        # Bloom filter says "maybe" - check Redis for confirmation
        redis_client = await get_redis_client()
        try:
            exists = await redis_client.exists(jti)
            result = exists == 1
            if result:
                logger("Auth", "Redis Cache", "WARN", "HIGH", f"Confirmed blacklisted token: {jti[:10]}...")
            return result
        finally:
            await redis_client.close()
    except Exception as e:
        logger("Auth", "Redis Cache", "ERROR", "ERROR", f"Token blacklist check failed: {str(e)}")
        return False

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