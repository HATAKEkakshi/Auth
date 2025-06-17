from fastapi import APIRouter, BackgroundTasks, Request, Depends, Form
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from model.model import User
from config.redis import add_jti_to_blacklist
from Dependenices.dependencies import get_access_token, User1Dep
from services.user2 import User2Service
from helper.utils import TEMPLATE_DIR
from config.notification import app_settings

user = APIRouter(prefix="/User2", tags=["User2"])

user_service = User2Service(model=User)
templates = Jinja2Templates(TEMPLATE_DIR)


@user.get("/")
async def get_user(id: str, request: Request, _: User1Dep):
    return await user_service.get_user(id, request)


@user.post("/create")
async def create_user(user_data: User, request: Request, tasks: BackgroundTasks):
    return await user_service.create_user(user_data, request, tasks)


@user.post("/login")
async def login_user(request:Request,request_form: OAuth2PasswordRequestForm = Depends()):
    token = await user_service.token(request_form.username, request_form.password,request)
    return {"access_token": token, "token_type": "bearer"}


@user.get("/verify")
async def verify_email(token: str, request: Request):
    is_success = await user_service.verify_email_token(token, request)
    return templates.TemplateResponse(
        request=request,
        name="email_verified.html" if is_success else "email_verified_failed.html"
    )


@user.get("/forget_password")
async def forget_password(email: str, tasks: BackgroundTasks):
    await user_service.forget_password(email, tasks)
    return {"message": "Password reset link sent to your email"}


@user.get("/reset_password_form")
async def reset_password_form(token: str, request: Request):
    return templates.TemplateResponse(
        name="reset.html",
        context={
            "request": request,
            "token": token,
            "reset_url": f"http://{app_settings.APP_DOMAIN}{user.prefix}/reset_password?token={token}"
        }
    )


@user.post("/reset_password")
async def reset_password(
    token: str,
    password: Annotated[str, Form()],
    request: Request,
    tasks: BackgroundTasks
):
    is_success = await user_service.reset_password_link(token, password, request, tasks)
    return templates.TemplateResponse(
        request=request,
        name="reset_success.html" if is_success else "reset_failed.html"
    )

@user.post("/otp_phone")
async def otp_phone(id:str,phone: str, request: Request):
    return await user_service.generate_otp_phone(id,phone,request)
@user.get("/verify_otp_phone")
async def verify_otp_phone(token: str, otp: int, request: Request):
    return await user_service.verify_otp_phone(token, otp, request)
@user.get("/logout")
async def logout(token_data: Annotated[dict, Depends(get_access_token)]):
    await add_jti_to_blacklist(token_data["jti"])
    return {"message": "Logout successfully"}


@user.delete("/delete")
async def delete_user(id: str, email: str, request: Request, _: User1Dep):
    return await user_service.delete_user(id, email, request)
