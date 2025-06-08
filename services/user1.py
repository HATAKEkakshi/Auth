from model.model import User
from helper.utils import password_hash, generate_country,id_generator,password_context,generate_access_token
from schema.schemas import individual_serializer
from fastapi import HTTPException, status,Request
from config.database import user1_collection_name
import json
class UserService:
    async def create_user(self, user_data: User,request:Request):
        redis=request.app.state.redis
        cache_key= f"user1:{user_data.email}"
        # Email Checking 
        cached=await redis.get(cache_key)
        if cached:
            return {"message": "Email already exists", "Email": user_data.email}
        if not cached:
            existing_user = await user1_collection_name.find_one({"email": user_data.email})
            if existing_user:
                return {"message": "Email already exists", "Email": user_data.email}
            else:
                # Hash password
                user_data.password = password_hash(user_data.password)
                # Generate id & country here
                user_dict = user_data.dict()
                user_id= id_generator()
                user_dict['id'] = user_id
                cache_id_key=f"user1:id:{user_id}"
                user_dict['country'] = generate_country(user_dict['country_code'])
                # Save to DB
                await user1_collection_name.insert_one(user_dict)
                user_dict.pop("_id", None)
                await redis.set(cache_key, json.dumps(user_dict), ex=3600)
                await redis.set(cache_id_key, json.dumps(user_dict), ex=3600)
                # Return serialized data (you may want to construct UserCreate with full data)
                return {"message": "User created successfully",
                    "Email":user_data.email}
    async def get_user(self, id: str,request:Request):
        redis=request.app.state.redis
        cache_key=f"user1:id:{id}"
        cached=await redis.get(cache_key)
        if cached:
            return json.loads(cached)
        user=await user1_collection_name.find_one({"id": id})
        if user:
            # Clean up _id before caching
             if "_id" in user:
                user["_id"] = str(user["_id"])  # OR use `user.pop("_id")` to completely remove
                user.pop("_id", None)
                await redis.set(cache_key, json.dumps(user), ex=3600)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {id} not found"
            )
        return individual_serializer(user)
    async def delete_user(self, id: str, email: str, request: Request):
        redis = request.app.state.redis
        cache_key = f"user1:id:{id}"
        cache_email_key = f"user1:{email}"

        # Delete cached entries if present
        await redis.delete(cache_key)
        await redis.delete(cache_email_key)

        # Check if user exists
        user = await user1_collection_name.find_one({"id": id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {id} not found"
            )

        # Perform deletion
        await user1_collection_name.delete_one({"id": id})

        return {
            "message": f"User with id {id} and email {email} deleted successfully"
        }
    async def token(self,email,password)->str:
        user= await user1_collection_name.find_one({"email": email})
        if user is None or not password_context.verify(password, user['password']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        token = generate_access_token({
        "id": user["id"],
        "email": user["email"],
        })
        return token

