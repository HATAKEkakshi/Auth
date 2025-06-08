from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
from routes.user1 import user as user1_router
from routes.user2 import user as user2_router
from redis.asyncio import Redis
import httpx
from fastapi import APIRouter


app=FastAPI()
#Create master router
master_router=APIRouter()
master_router.include_router(user1_router)
master_router.include_router(user2_router)
#Including master router in the app
app.include_router(master_router)

@app.on_event("startup")
async def startup():
    app.state.redis = Redis(host="localhost", port=6379, decode_responses=True)
    app.state.http_client = httpx.AsyncClient()

@app.on_event("shutdown")
async def shutdown():
    await app.state.redis.close()
    await app.state.http_client.aclose()
@app.get("/scalar", include_in_schema=False)
def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API"
    )