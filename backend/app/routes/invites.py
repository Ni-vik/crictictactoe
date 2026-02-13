from fastapi import APIRouter, HTTPException,status,Depends
from datetime import datetime, timedelta 
from uuid import uuid4 
from typing import Optional

from models.invites import GameInvite,InviteCreate,InviteResponse
from database.db import invites_collection, games_collection
from app.deps.auth import get_current_user

router = APIRouter(prefix="/invites",tags=["Invites"])

@router.post("/create",response_model=InviteResponse,status_code=status.HTTP_201_CREATED)
async def create_invite(current_user = Depends(get_current_user)):

    invite_id = uuid4()

    invite_doc = {
        "invite_id" : str(invite_id),
        "created_by" : current_user["user_id"],
        "created_by_username" : current_user["username"],
        "joined_by" : None,
        "status" : "pending",
        "expires_at" :datetime.utcnow() + timedelta(hours=24),
        "created_at" : datetime.utcnow(),
        "game_id" : None
    } 
    await invites_collection.insert_one(invite_doc)

    invite_link = f"https://yourdomain.com/game/invite/{invite_id}"
    return{
        "invite_id" : str(invite_id),
        "invite_link" : invite_link,
        "expires_at" : invite_doc["expires_at"],
        "status" : invite_doc["status"]
    }

@router.get("/{invite_id}", response_model=dict)
async def get_invite(invite_id: str):
    """Get invite details"""
    invite = await invites_collection.find_one({"invite_id": invite_id})
    
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )
    
    # Check if expired
    if invite["expires_at"] < datetime.utcnow():
        await invites_collection.update_one(
            {"invite_id": invite_id},
            {"$set": {"status": "expired"}}
        )
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Invite has expired"
        )
    
    if invite["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invite is {invite['status']}"
        )
    
    return {
        "invite_id": invite["invite_id"],
        "created_by_username": invite["created_by_username"],
        "created_at": invite["created_at"],
        "expires_at": invite["expires_at"]
    }

@router.post("/{invite_id}/accept", status_code=status.HTTP_200_OK)
async def accept_invite(invite_id: str, current_user: dict = Depends(get_current_user)):
    """Accept an invite and create a game"""
    invite = await invites_collection.find_one({"invite_id": invite_id})
    
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )
    
    # Validation checks
    if invite["created_by"] == current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot accept your own invite"
        )
    
    if invite["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invite is {invite['status']}"
        )
    
    if invite["expires_at"] < datetime.utcnow():
        await invites_collection.update_one(
            {"invite_id": invite_id},
            {"$set": {"status": "expired"}}
        )
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Invite has expired"
        )
    
    # Create game
    game_id = uuid4()
    game_doc = {
        "game_id": str(game_id),
        "player1_id": invite["created_by"],
        "player2_id": current_user["user_id"],
        "current_turn": invite["created_by"],  # Creator goes first
        "board": [""] * 9,  # Empty tic-tac-toe board
        "status": "waiting",  # waiting, in_progress, completed
        "winner": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await games_collection.insert_one(game_doc)
    
    # Update invite
    await invites_collection.update_one(
        {"invite_id": invite_id},
        {
            "$set": {
                "joined_by": current_user["user_id"],
                "status": "accepted",
                "game_id": str(game_id)
            }
        }
    )
    
    return {
        "message": "Invite accepted",
        "game_id": str(game_id)
    }