from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from database.db import players_collection

router = APIRouter(prefix="/players", tags=["Players"])

@router.get("/search", response_model=List[dict])
async def search_players(q: str = Query(..., min_length=1)):
    """
    Search for players by name.
    Returns a list of matching players (max 10).
    """
    if not q:
        return []

    # Case-insensitive regex search
    # We'll match any part of the name
    cursor = players_collection.find({
        "player_name": {"$regex": q, "$options": "i"}
    }).limit(10)
    
    players = await cursor.to_list(length=10)
    
    # Return serializable format
    # We only really need the name for the game logic
    return [
        {
            "player_name": p["player_name"],
             # Include other fields if useful for UI, e.g. team/country to disambiguate
            "country": p.get("Country"),
            "ipl_teams": p.get("IPL Teams")
        } 
        for p in players
    ]
