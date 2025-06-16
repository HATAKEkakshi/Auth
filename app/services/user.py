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

    async def _get(self, id: str, request: Request, collection_name, redis_key_prefix: str):
        redis = request.app.state.redis
        cache_key = f"{redis_key_prefix}:id:{id}"
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        user = await collection_name.find_one({"id": id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {id} not found"
            )

        user.pop("_id", None)
        await redis.set(cache_key, json.dumps(user), ex=3600)
        return user

    async def _add(
        self,
        user_data,
        request: Request,
        collection_name,
        redis_key_prefix: str,
        tasks: BackgroundTasks,
        router_prefix: str
    ):
        redis = request.app.state.redis
        cache_key = f"{redis_key_prefix}:{user_data.email}"

        if await redis.get(cache_key) or await collection_name.find_one({"email": user_data.email}):
            return {"message": "Email already exists", "Email": user_data.email}

        # Hash password and enrich data
        user_data.password = password_hash(user_data.password)
        user_dict = user_data.dict()
        user_id = id_generator()
        user_dict.update({
            "id": user_id,
            "country": generate_country(user_dict["country_code"]),
            "is_email_verified": False
        })

        await collection_name.insert_one(user_dict)
        user_dict.pop("_id", None)

        await redis.set(cache_key, json.dumps(user_dict), ex=3600)
        await redis.set(f"{redis_key_prefix}:id:{user_id}", json.dumps(user_dict), ex=3600)

        # Generate verification token
        token = generate_url_safe_token(
            {"email": user_data.email, "id": user_id},
            salt=self.verification_salt
        )

        # Send emails
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

    async def verify_email(self, token: str, collection_name, request: Request, redis_key_prefix: str):
        token_data = decode_url_safe_token(token, salt=self.verification_salt)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token"
            )

        user = await self._get(token_data["id"], request, collection_name, redis_key_prefix)
        user["is_email_verified"] = True

        await collection_name.update_one({"id": user["id"]}, {"$set": {"is_email_verified": True}})

        redis = request.app.state.redis
        await redis.delete(f"{redis_key_prefix}:id:{user['id']}")
        await redis.set(f"{redis_key_prefix}:{user['email']}", json.dumps(user))

        return True

    async def _delete_user(self, id: str, email: str, request: Request, collection_name, redis_key_prefix: str):
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

    async def _token(self, email: str, password: str, collection_name) -> str:
        user = await collection_name.find_one({"email": email})
        if not user or not password_context.verify(password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        if not user.get("is_email_verified", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified"
            )

        return generate_access_token({
            "id": user["id"],
            "email": user["email"]
        })

    async def _send_password_reset_link(self, email: str, router_prefix: str, collection_name, tasks: BackgroundTasks):
        user = await collection_name.find_one({"email": email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        token = generate_url_safe_token(
            {"id": user["id"]},
            salt=self.verification_salt
        )

        self.notification_service.send_email_template(
            tasks,
            email=email,
            subject="Password Reset Request",
            context={
                "name": user["first_name"],
                "reset_url": f"http://{app_settings.APP_DOMAIN}/{router_prefix}/reset_password_form?token={token}"
            },
            template_name="mail_password_reset.html"
        )

        return {"message": "Password reset link sent to your email"}

    async def reset_password(self, token: str, password: str, collection_name, request: Request, redis_key_prefix: str, tasks: BackgroundTasks):
        token_data = decode_url_safe_token(token, salt=self.verification_salt)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token"
            )

        user = await collection_name.find_one({"id": token_data["id"]})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user["password"] = password_hash(password)
        await collection_name.update_one({"id": user["id"]}, {"$set": {"password": user["password"]}})

        redis = request.app.state.redis
        await redis.delete(f"{redis_key_prefix}:id:{user['id']}")
        await redis.delete(f"{redis_key_prefix}:{user['email']}")

        return {"message": "Password reset successfully"}
