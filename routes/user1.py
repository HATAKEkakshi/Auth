from fastapi import APIRouter,Request,Depends
from model.model import User
from typing import Annotated
from services.user1 import UserService
from fastapi.security import OAuth2PasswordRequestForm
from Dependenices.dependencies import User1Dep
user=APIRouter(prefix="/User1",tags=["User1"])
user_service=UserService()
@user.get("/")
async def get_user(id:str,request:Request,_: User1Dep):
    return await user_service.get_user(id,request)
@user.post("/create")
async def create_user(user_data:User,request:Request):
    return await user_service.create_user(user_data,request)
@user.post("/login")
async def login_user(request_form:Annotated[OAuth2PasswordRequestForm,Depends()]):
    token=await user_service.token(request_form.username,request_form.password)
    return {"access_token": token, "token_type": "bearer"}

@user.delete("/delete")
async def delete_user(id: str, email: str, request: Request):
    return await user_service.delete_user(id, email, request)