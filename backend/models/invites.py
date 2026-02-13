from pydantic import  BaseModel
from datetime import datetime
from typing import Optional

class GameInvite(BaseModel):
    invite_id : str
    created_by : str
    created_by_username : str
    joined_by : Optional[str] = None
    status : str
    expires_at : datetime
    created_at : datetime
    game_id :  Optional[str] = None

class InviteResponse(BaseModel):
    invite_id:str
    invite_link:str
    expires_at : datetime
    status:str

class InviteCreate(BaseModel):
    """Request body for creating an invite"""
    user_id: str
    username: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "username": "cricket_fan_99"
            }
        }
