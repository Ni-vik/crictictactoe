from pydantic import  BaseModel,EmailStr,Field,field_validator
from typing import Optional
from datetime import datetime
import re

class UserInDB(BaseModel):
    user_id :str
    name : str
    email :EmailStr
    password_hash : str
    wins : int = Field(0,ge = 0)
    losses : int = Field(0,ge = 0)
    draws : int = Field(0,ge= 0)
    status : str
    created_at : datetime

class UserSignUp(BaseModel):
    """Model for user registration"""
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=8,max_length=20)
    
    @field_validator('username')
    def username_alphanumeric(cls, v):
        """Username must be alphanumeric (can include underscore)"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must be alphanumeric (can include underscore)')
        return v.lower()  # Store as lowercase
    
    @field_validator('password')
    def password_strength(cls, v):
        """Validate password strength"""
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes")
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "cricket_fan_99",
                "email": "user@example.com",
                "password": "Password123"
            }
        }

class UserLogin(BaseModel):
    """Model for user login"""
    username_or_email: str = Field(..., description="Username or email")
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "username_or_email": "cricket_fan_99",
                "password": "Password123"
            }
        }


