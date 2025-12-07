from pydantic import BaseModel, EmailStr, Field


class UserRegistrationSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, description="The user's username")
    email: EmailStr = Field(..., description="The user's email address")
    password: str = Field(..., min_length=8, description="The user's password")
    phone: str = Field(
        ...,
        regex=r'^\+?[1-9]\d{1,14}$',
        description="The user's phone number in international format"
    )


class UserLoginSchema(BaseModel):
    username: str = Field(..., description="The user's username")
    password: str = Field(..., description="The user's password")
