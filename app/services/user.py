from fastapi import BackgroundTasks, HTTPException, Request, status
from services.notifications import NotificationService
from helper.utils import (
    generate_country, id_generator, password_hash,
    password_context, generate_access_token
)
from model.model import User
import json

class UserService:
    def __init__(self, model: User):
        self.model = model
        self.notification_service = NotificationService()

    async def _get(self, id: str, request: Request, collection_name: str, redis_key_prefix: str):
        redis = request.app.state.redis
        cache_key = f"{redis_key_prefix}:id:{id}"
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)
        user = await collection_name.find_one({"id": id})
        if user:
            user.pop("_id", None)
            await redis.set(cache_key, json.dumps(user), ex=3600)
            return user
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} not found"
        )

    async def _add(
        self, 
        user_data: User, 
        request: Request, 
        collection_name: str, 
        redis_key_prefix: str,
        tasks: BackgroundTasks  # ✅ pass tasks here!
    ):
        redis = request.app.state.redis
        cache_key = f"{redis_key_prefix}:{user_data.email}"
        cached = await redis.get(cache_key)
        if cached:
            return {"message": "Email already exists", "Email": user_data.email}
        existing_user = await collection_name.find_one({"email": user_data.email})
        if existing_user:
            return {"message": "Email already exists", "Email": user_data.email}

        # Create new user
        user_data.password = password_hash(user_data.password)
        user_dict = user_data.dict()
        user_id = id_generator()
        user_dict['id'] = user_id
        user_dict['country'] = generate_country(user_dict['country_code'])
        await collection_name.insert_one(user_dict)
        user_dict.pop("_id", None)
        await redis.set(cache_key, json.dumps(user_dict), ex=3600)
        await redis.set(f"{redis_key_prefix}:id:{user_id}", json.dumps(user_dict), ex=3600)

        # ✅ Use new NotificationService properly — pass tasks here:
        self.notification_service.send_email_template(
            tasks=tasks,
            email=user_data.email,
            subject="Registration Successful",
            context={
                "name": user_data.first_name
            },
            template_name="registration.html"
        )

        return {
            "message": "User created successfully",
            "Email": user_data.email,
            "id": user_id
        }

    async def _delete_user(self, id: str, email: str, request: Request, collection_name: str, redis_key_prefix: str):
        redis = request.app.state.redis
        await redis.delete(f"{redis_key_prefix}:id:{id}")
        await redis.delete(f"{redis_key_prefix}:{email}")
        user = await collection_name.find_one({"id": id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {id} not found"
            )
        await collection_name.delete_one({"id": id})
        return {"message": f"User with id {id} and email {email} deleted successfully"}

    async def _token(self, email, password, collection_name: str) -> str:
        user = await collection_name.find_one({"email": email})
        if not user or not password_context.verify(password, user['password']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        return generate_access_token({"id": user["id"], "email": user["email"]})
