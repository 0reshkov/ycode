from fastapi import APIRouter

from src.ycode.schemas.auth import UserRegistrationSchema, UserLoginSchema

auth_router = APIRouter()


@auth_router.post("/register")
async def register(user: UserRegistrationSchema):
    return {"message": "Register endpoint"}


@auth_router.post("/login")
async def login(user: UserLoginSchema):
    return {"message": "Login endpoint"}


@auth_router.post("/refresh")
async def refresh():
    return {"message": "Refresh endpoint"}


@auth_router.post("/logout")
async def logout():
    return {"message": "Logout endpoint"}
