from fastapi import Request
from model.model import User
from .user import UserService
from config.database import user2_collection_name

# ✅ Correct instantiation
#user_service = User1Service(model=User)
class User2Service(UserService):
    def __init__(self, model: User):
        super().__init__(model)
        self.model = model
        self.collection_name = user2_collection_name
        self.redis_key_prefix = "user2"

    async def create_user(self, user_data: User, request: Request):
        return await self._add(
            user_data, request, 
            self.collection_name, 
            self.redis_key_prefix
        )

    async def get_user(self, id: str, request: Request):
        return await self._get(
            id, request, 
            self.collection_name, 
            self.redis_key_prefix
        )

    async def delete_user(self, id: str, email: str, request: Request):
        return await self._delete_user(
            id, email, request, 
            self.collection_name, 
            self.redis_key_prefix
        )

    async def token(self, email: str, password: str):
        return await self._token(
            email, password, 
            self.collection_name
        )



