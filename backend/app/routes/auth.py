from fastapi import APIRouter, HTTPException,status
from datetime import datetime
from uuid import uuid4

from models.users import UserSignUp
from database.db import users_collection
from app.security import hash_password

router = APIRouter(prefix="/auth" , tags = ["Auth"])

@router.post("/signup",status_code = status.HTTP_201_CREATED)
async def signup(user : UserSignUp):

    # Case-insensitive username check
    existing_username = await users_collection.find_one({
        "username": {"$regex": f"^{user.username}$", "$options": "i"}
    })

    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )
    
    # Only check email if provided
    if user.email:
        existing_email = await users_collection.find_one({
            "email": {"$regex": f"^{user.email}$", "$options": "i"}
        })

        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
    
    user_doc = {
        "user_id": str(uuid4()),
        "username": user.username,
        "email": user.email,
        "password_hash": hash_password(user.password),
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "status": "active",
        "created_at": datetime.utcnow(),
    }

    await users_collection.insert_one(user_doc)

    return {
        "message" : "User created successfully",
        "user_id" : user_doc["user_id"],
        "username" : user.username
    }