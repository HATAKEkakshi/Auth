from fastapi import APIRouter,Request,Depends
from config.redis import add_jti_to_blacklist
from model.model import User
from services.user2 import User2Service
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from Dependenices.dependencies import User2Dep, get_access_token
user=APIRouter(prefix="/User2",tags=["User2"])
user_service=User2Service(model=User)
@user.get("/")
async def get_user(id: str,request: Request,_:User2Dep):
    return await user_service.get_user(id,request)
@user.post("/create")
async def create_user(user_data: User,request: Request):
    return await user_service.create_user(user_data,request)
@user.post("/login")
async def login_user(request_form:Annotated[OAuth2PasswordRequestForm,Depends()]):
    token=await user_service.token(request_form.username,request_form.password)
    return {"access_token": token, "token_type": "bearer"}
@user.get("/logout")
async def logout(token_data:Annotated[dict,Depends(get_access_token)]):
    print(token_data)
    await add_jti_to_blacklist(token_data["jti"])
    return {"message": "Logout successfully"}
@user.delete("/delete")
async def delete_user(id: str, email: str, request: Request,_:User2Dep):
    return await user_service.delete_user(id, email, request)