from fastapi import APIRouter,HTTPException,status
from datetime import datetime

from database.db import users_collection
from models.users import UserLogin
from app.security import verify_password
from app.utils.jwt import create_access_token

router = APIRouter(prefix="/auth",tags=["Auth"])

@router.post("/login")
async def login(payload: UserLogin):
    user = await users_collection.find_one({
        "$or":[
            {"username" : payload.username_or_email.lower()},
            {"email"  : payload.username_or_email.lower()}
        ]
    }) 

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not verify_password(payload.password,user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials"
        )
    
    token = create_access_token(
        {"sub" : user["user_id"]}
    )

    return {
        "access_token" : token,
        "token_type" : "bearer"
    }