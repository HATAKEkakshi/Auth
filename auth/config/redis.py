from redis.asyncio import Redis, ConnectionPool
from typing import Optional, Dict, Any
import json
import asyncio
from auth.config.database import db_settings
from auth.logger.log import logger
from auth.config.bloom import bloom_service
from auth.security.cache_encryption import CacheEncryptionService

# Redis connection pool singleton for thread-safe access
class RedisPoolManager:
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_pool(self):
        if self._pool is None:
            self._pool = ConnectionPool(
                host=db_settings.REDIS_HOST,
                port=db_settings.REDIS_PORT,
                db=0,
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True
            )
            logger("Auth", "Redis Pool", "INFO", "null", "Redis connection pool initialized")
        return self._pool

_pool_manager = RedisPoolManager()

"""Get Redis client from connection pool"""
async def get_redis_client():
    pool = await _pool_manager.get_pool()
    return Redis(connection_pool=pool)

"""Set encrypted data in Redis cache with expiration time"""
async def set_profile_data(key: str, ttl: int, profile_data: dict):
    redis_client = await get_redis_client()
    try:
        # Encrypt sensitive data before caching
        encrypted_data = CacheEncryptionService.encrypt_cache_data(profile_data)
        await redis_client.setex(key, ttl, encrypted_data)
        logger("Auth", "Redis Cache", "INFO", "null", f"Setting encrypted data for key in cache: {key} with TTL: {ttl}")
    except Exception as e:
        logger("Auth", "Redis Cache", "ERROR", "HIGH", f"Redis error: {e}")
        raise

"""Get and decrypt data from Redis cache by key"""
async def get_profile_data(key: str) -> Optional[dict]:
    redis_client = await get_redis_client()
    try:
        encrypted_data = await redis_client.get(key)
        if encrypted_data:
            # Decrypt cached data
            decrypted_data = CacheEncryptionService.decrypt_cache_data(encrypted_data)
            logger("Auth", "Redis Cache", "INFO", "null", f"Cache hit getting encrypted data for key from cache: {key}")
            return decrypted_data
        logger("Auth", "Redis Cache", "WARN", "LOW", f"Cache miss for key: {key}")
        return None
    except Exception as e:
        logger("Auth", "Redis Cache", "ERROR", "HIGH", "Redis decryption error")
        return None

"""Delete data from Redis cache by key"""
async def delete_profile_data(key: str):
    redis_client = await get_redis_client()
    try:
        await redis_client.delete(key)
        logger("Auth", "Redis Cache", "INFO", "null", f"Deleted data for key in cache: {key}")
    except Exception as e:
        logger("Auth", "Redis Cache", "ERROR", "ERROR", f"Redis error: {e}")
        raise

"""Add JWT token to blacklist with Bloom filter optimization"""
async def add_jti_to_blacklist(jti: str):
    redis_client = await get_redis_client()
    try:
        # Add to both Bloom filter and Redis with TTL (24 hours)
        bloom_service.add_blacklisted_token(jti)
        await redis_client.setex(jti, 86400, "blacklisted")
        logger("Auth", "Redis Cache", "INFO", "null", f"Token blacklisted with Bloom filter: {jti[:10]}...")
    except Exception as e:
        logger("Auth", "Redis Cache", "ERROR", "ERROR", f"Failed to blacklist token: {str(e)}")
        raise

"""Check if JWT token is blacklisted using Bloom filter first"""
async def is_jti_blacklisted(jti: str) -> bool:
    try:
        # Fast Bloom filter check first
        if not bloom_service.is_token_blacklisted(jti):
            # Definitely not blacklisted
            return False
        
        # Bloom filter says "maybe" - check Redis for confirmation
        redis_client = await get_redis_client()
        exists = await redis_client.exists(jti)
        result = exists == 1
        if result:
            logger("Auth", "Redis Cache", "WARN", "HIGH", f"Confirmed blacklisted token: {jti[:10]}...")
        return result
    except Exception as e:
        logger("Auth", "Redis Cache", "ERROR", "HIGH", "Token blacklist check failed")
        return False

"""Check Redis connection health status"""
async def check_redis_health():
    redis_client = None
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        logger("Auth", "Redis Cache", "INFO", "null", "Redis connection successful")
        return True
    except Exception as e:
        logger("Auth", "Redis Cache", "ERROR", "CRITICAL", f"Redis connection failed: {str(e)}")
        return False

"""Continuously monitor Redis health every 60 seconds with error handling"""
async def monitor_redis():
    while True:
        try:
            await check_redis_health()
            await asyncio.sleep(60)
        except Exception as e:
            logger("Auth", "Redis Monitor", "ERROR", "HIGH", f"Redis monitoring error: {str(e)}")
            await asyncio.sleep(60)
# Global task reference to prevent garbage collection
_monitoring_task = None

"""Initialize Redis health monitoring as background task"""
def start_redis_monitoring():
    global _monitoring_task
    if _monitoring_task is None or _monitoring_task.done():
        _monitoring_task = asyncio.create_task(monitor_redis())
        logger("Auth", "Redis Monitor", "INFO", "null", "Redis monitoring task started")
    return _monitoring_task