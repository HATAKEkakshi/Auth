from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.auth
user1_collection_name=db["User1"]
user2_collection_name=db["User2"]

