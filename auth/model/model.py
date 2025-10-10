from pydantic import BaseModel, Field, EmailStr, root_validator
from typing import Optional
from auth.helper.utils import id_generator

class BaseUser(BaseModel):
    id: str = Field(default_factory=id_generator, description="User ID")

class User(BaseModel):
    first_name: str = Field(..., description="First Name")
    last_name: str = Field(..., description="Last Name")
    email: EmailStr = Field(..., description="Email Address")
    phone: str = Field(..., description="Phone Number")
    country_code: str = Field(..., description="Country Code")
    password: str = Field(..., description="Password")
    is_email_verified: bool = Field(default=False, description="Email Verification Status")
    # country is not expected from client input, so exclude here
