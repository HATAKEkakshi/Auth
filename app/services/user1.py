from fastapi import BackgroundTasks, Request
from model.model import User
from .user import UserService
from config.database import user1_collection_name

class User1Service(UserService):
    def __init__(self, model: User):
        super().__init__(model)
        self.collection_name = user1_collection_name
        self.redis_key_prefix = "user1"
        self.router_prefix = "User1"  # ✅ Used for email verification link

    async def create_user(self, user_data: User, request: Request, tasks: BackgroundTasks):
        return await self._add(
            user_data,
            request,
            self.collection_name,
            self.redis_key_prefix,
            tasks,
            self.router_prefix  # ✅ Pass router prefix here!
        )

    async def get_user(self, id: str, request: Request):
        return await self._get(
            id,
            request,
            self.collection_name,
            self.redis_key_prefix
        )

    async def delete_user(self, id: str, email: str, request: Request):
        return await self._delete_user(
            id,
            email,
            request,
            self.collection_name,
            self.redis_key_prefix
        )

    async def token(self, email: str, password: str):
        return await self._token(
            email,
            password,
            self.collection_name
        )

    async def verify_email_token(self, token: str, request: Request):
        return await self.verify_email(
            token,
            self.collection_name,
            request,
            self.redis_key_prefix
        )
