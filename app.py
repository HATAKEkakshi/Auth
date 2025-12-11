from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
from auth.routes.user1 import user as user1_router
from auth.routes.user2 import user as user2_router
from redis.asyncio import Redis
import httpx
from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from auth.config.database import start_db_monitoring,db_settings
from auth.config.redis import start_redis_monitoring, init_redis_pool, check_redis_health
from auth.config.database import check_database_health
from auth.middleware.security import SecurityMiddleware
import uvicorn

app=FastAPI()

# Security Middleware (first for maximum protection)
app.add_middleware(SecurityMiddleware, rate_limit_requests=100, rate_limit_window=3600)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8010", 
        "http://127.0.0.1:8010",
        "https://yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-CSRF-Token",
    ],
    expose_headers=["X-Total-Count", "X-Page-Count"],
    max_age=600,
)

"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""
#Create master router
master_router=APIRouter()
master_router.include_router(user1_router)
master_router.include_router(user2_router)
#Including master router in the app
app.include_router(master_router)

@app.on_event("startup")
async def startup():
    # Initialize Redis connection pool
    await init_redis_pool()
    app.state.http_client = httpx.AsyncClient()
    start_db_monitoring() # Start monitoring the database
    start_redis_monitoring() # Start monitoring Redis

@app.on_event("shutdown")
async def shutdown():
    await app.state.http_client.aclose()
@app.get("/health")
async def health_check():
    """System health check endpoint"""
    db_healthy = await check_database_health()
    redis_healthy = await check_redis_health()
    
    return {
        "status": "healthy" if db_healthy and redis_healthy else "unhealthy",
        "database": "healthy" if db_healthy else "unhealthy",
        "redis": "healthy" if redis_healthy else "unhealthy"
    }

@app.get("/scalar", include_in_schema=False)
def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)