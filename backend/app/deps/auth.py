from fastapi import Depends,HTTPException,status
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from jose import JWTError
from app.utils.jwt import decode_access_token
from database.db import users_collection

security = HTTPBearer()
async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = payload.get('sub')
        if not user_id:
            raise ValueError
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid or expired token"
        )
    user = await users_collection.find_one({
        "user_id" : user_id
    })
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user