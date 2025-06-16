from fastapi import BackgroundTasks, Request
from model.model import User
from .user import UserService
from config.database import user2_collection_name

class User2Service(UserService):
    def __init__(self, model: User):
        super().__init__(model)
        self.collection_name = user2_collection_name
        self.redis_key_prefix = "user2"
        self.router_prefix = "User2"

    async def create_user(self, user_data: User, request: Request, tasks: BackgroundTasks):
        return await self._add(
            user_data,
            request,
            self.collection_name,
            self.redis_key_prefix,
            tasks,
            self.router_prefix
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

    async def forget_password(self, email: str, tasks: BackgroundTasks):
        return await self._send_password_reset_link(
            email=email,
            router_prefix=self.router_prefix,
            collection_name=self.collection_name,
            tasks=tasks
        )

    async def reset_password_link(self, token: str, password: str, request: Request, tasks: BackgroundTasks):
        return await self.reset_password(
            token,
            password,
            self.collection_name,
            request,
            self.redis_key_prefix,
            tasks
        )
    async def generate_otp_phone(self, id, phone, request):
        return await self.generate_otp(id, phone, request, self.collection_name, self.redis_key_prefix)
    async def verify_otp_phone(self, token, otp, request):
        return await super().verify_otp(token, otp, request)