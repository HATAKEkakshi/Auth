from fastapi import APIRouter,Request
from model.model import User
from services.user1 import UserService

user=APIRouter(prefix="/User1",tags=["User1"])
user_service=UserService()
@user.get("/")
async def get_user(id:str,request:Request):
    return await user_service.get_user(id,request)
@user.post("/create")
async def create_user(user_data:User,request:Request):
    return await user_service.create_user(user_data,request)


@user.delete("/delete")
async def delete_user(id: str, email: str, request: Request):
    return await user_service.delete_user(id, email, request)