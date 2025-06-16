from fastapi import BackgroundTasks, HTTPException, Request, status
from config.notification import app_settings
from services.notifications import NotificationService
from helper.utils import (
    generate_country, id_generator, password_hash,
    password_context, generate_access_token,
    generate_url_safe_token, decode_url_safe_token
)
import json


class UserService:
    def __init__(self, model):
        self.model = model
        self.notification_service = NotificationService()
        self.verification_salt = "email-verify"

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
        user_data,
        request: Request,
        collection_name: str,
        redis_key_prefix: str,
        tasks: BackgroundTasks,
        router_prefix: str
    ):
        redis = request.app.state.redis
        cache_key = f"{redis_key_prefix}:{user_data.email}"

        # Check cache and DB for duplicates
        if await redis.get(cache_key) or await collection_name.find_one({"email": user_data.email}):
            return {"message": "Email already exists", "Email": user_data.email}

        # Prepare new user
        user_data.password = password_hash(user_data.password)
        user_dict = user_data.dict()
        user_id = id_generator()
        user_dict['id'] = user_id
        user_dict['country'] = generate_country(user_dict['country_code'])

        await collection_name.insert_one(user_dict)
        user_dict.pop("_id", None)

        await redis.set(cache_key, json.dumps(user_dict), ex=3600)
        await redis.set(f"{redis_key_prefix}:id:{user_id}", json.dumps(user_dict), ex=3600)

        # Generate verification token with salt
        token = generate_url_safe_token(
            {"email": user_data.email, "id": user_id},
            salt=self.verification_salt
        )

        # ✅ Send both emails, with tasks
        self.notification_service.send_email_template(
            tasks=tasks,
            email=user_data.email,
            subject="Registration Successful",
            context={"name": user_data.first_name},
            template_name="registration.html"
        )

        self.notification_service.send_email_template(
            tasks=tasks,
            email=user_data.email,
            subject="Verify your email",
            context={
                "name": user_data.first_name,
                "verification_url": f"http://{app_settings.APP_DOMAIN}/{router_prefix}/verify?token={token}"
            },
            template_name="mail_email_verify.html"
        )

        return {
            "message": "User created successfully",
            "Email": user_data.email,
            "id": user_id
        }

    async def verify_email(self, token: str, collection_name: str, request: Request, redis_key_prefix: str):
        token_data = decode_url_safe_token(token, salt=self.verification_salt)
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token"
            )
        user = await self._get(token_data["id"], request, collection_name, redis_key_prefix)
        user["is_email_verified"] = True

        await collection_name.update_one({"id": user["id"]}, {"$set": user})
        redis = request.app.state.redis
        await redis.delete(f"{redis_key_prefix}:id:{user['id']}")
        await redis.set(f"{redis_key_prefix}:{user['email']}", json.dumps(user))

        return {"message": "Email verified successfully", "user": user}

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
                detail="Invalid email or password"
            )
        if not user["is_email_verified"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified"
            )
        return generate_access_token({
            "id": user["id"],
            "email": user["email"]
        })
