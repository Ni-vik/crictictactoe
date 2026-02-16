# routes/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query, status
from typing import Dict, List, Optional
from bson import ObjectId
from datetime import datetime
import random
from jose import JWTError

from database.db import games_collection, users_collection, players_collection
from app.services.game_engine import GameEngine
from app.utils.jwt import decode_access_token

router = APIRouter()

# ============================================
# Helper Function: Serialize MongoDB Documents
# ============================================

def serialize_doc(doc):
    """Convert MongoDB document to JSON-safe dict"""
    if doc is None:
        return None
    
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    
    if isinstance(doc, dict):
        serialized = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                serialized[key] = str(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = serialize_doc(value)
            elif isinstance(value, list):
                serialized[key] = serialize_doc(value)
            else:
                serialized[key] = value
        return serialized
    
    return doc


# ============================================
# WebSocket Connection Manager
# ============================================

class ConnectionManager:
    def __init__(self):
        # game_id -> {player_id: websocket}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, game_id: str, user_id: str):
        await websocket.accept()
        
        if game_id not in self.active_connections:
            self.active_connections[game_id] = {}
        
        self.active_connections[game_id][user_id] = websocket
    
    def disconnect(self, game_id: str, user_id: str):
        if game_id in self.active_connections:
            if user_id in self.active_connections[game_id]:
                del self.active_connections[game_id][user_id]
            
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast_to_game(self, message: dict, game_id: str):
        if game_id in self.active_connections:
            for connection in self.active_connections[game_id].values():
                await connection.send_json(message)

manager = ConnectionManager()


# ============================================
# WebSocket Endpoint
# ============================================

@router.websocket("/ws/game/{game_id}")
async def game_websocket(
    websocket: WebSocket, 
    game_id: str, 
    token: str = Query(...)
):
    """
    WebSocket endpoint for game interaction.
    Requires 'token' query parameter for authentication.
    """
    # 1. Authenticate User
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    # Verify user exists (optional, but good for consistency)
    user = await users_collection.find_one({"user_id": user_id})
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
        return

    # 2. Verify Game
    game = await games_collection.find_one({"game_id": game_id})
    if not game:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Game not found")
        return
    
    # 3. Verify Authorization (Player must be part of the game)
    if user_id not in [game["player1_id"], game["player2_id"]]:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Not authorized for this game")
        return
    
    # 4. Connect
    await manager.connect(websocket, game_id, user_id)
    
    # 5. Notify Join
    game_safe = serialize_doc(game)
    
    await manager.broadcast_to_game({
        "type": "player_joined",
        "user_id": user_id,
        "username": user["username"],
        "game_state": game_safe
    }, game_id)
    
    # Update game status if both players connected and status is 'waiting'
    # Note: This simple check might restart a completed game if not careful, 
    # but the logic checks if we just reached 2 connections.
    # Safe to assume if we are 'waiting' and now have 2, we start.
    if game["status"] == "waiting" and len(manager.active_connections.get(game_id, {})) == 2:
        # Fetch available teams for grid generation
        pipeline_ipl = [
            {"$unwind": "$IPL Teams"},
            {"$group": {"_id": "$IPL Teams"}},
            {"$sample": {"size": 6}}
        ]
        pipeline_country = [
            {"$group": {"_id": "$Country"}},
            {"$sample": {"size": 2}}
        ]
        
        ipl_teams_cursor = players_collection.aggregate(pipeline_ipl)
        national_teams_cursor = players_collection.aggregate(pipeline_country)
        
        ipl_teams = [doc["_id"] async for doc in ipl_teams_cursor]
        national_teams = [doc["_id"] async for doc in national_teams_cursor]
        
        # Fallback if not enough data (mostly for testing/robustness)
        if len(ipl_teams) < 4:
            # Add placeholders if DB is empty
            ipl_teams += [f"IPL_Team_{i}" for i in range(4 - len(ipl_teams))]
        if len(national_teams) < 2:
            national_teams += [f"Country_{i}" for i in range(2 - len(national_teams))]
            
        grid_headers = GameEngine.generate_grid_headers(ipl_teams, national_teams)
        
        await games_collection.update_one(
            {"game_id": game_id},
            {"$set": {
                "status": "in_progress",
                "grid_headers": grid_headers
            }}
        )
        await manager.broadcast_to_game({
            "type": "game_start",
            "message": "Both players connected. Game started!",
            "grid_headers": grid_headers,
            "timestamp": datetime.utcnow().isoformat()
        }, game_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "make_move":
                position = data["position"]
                
                # Fetch fresh game state
                game = await games_collection.find_one({"game_id": game_id})
                
                # Check if game has grid headers (legacy games might not)
                grid_headers = game.get("grid_headers")
                guessed_player_name = data.get("player_guess")
                
                if not grid_headers:
                     await manager.send_personal_message({
                        "type": "error",
                        "message": "Game grid not initialized."
                    }, websocket)
                     continue

                if not guessed_player_name:
                     await manager.send_personal_message({
                        "type": "error",
                        "message": "You must guess a player name."
                    }, websocket)
                     continue
                
                # Look up player in DB
                # Case-insensitive regex search for exact match preferred or just case-insensitive
                # "player_name" field in DB
                player_doc = await players_collection.find_one(
                    {"player_name": {"$regex": f"^{guessed_player_name}$", "$options": "i"}}
                )
                
                if not player_doc:
                     await manager.send_personal_message({
                        "type": "error",
                        "message": f"Player '{guessed_player_name}' not found in database."
                    }, websocket)
                     continue
                     
                # Determine Row/Col criteria based on position
                # 0 1 2 -> Row 0
                # 3 4 5 -> Row 1
                # 6 7 8 -> Row 2
                # Cols: pos % 3
                row_idx = position // 3
                col_idx = position % 3
                
                row_criteria = grid_headers["rows"][row_idx]
                col_criteria = grid_headers["cols"][col_idx]
                
                # Validate Move using GameEngine (Logic + Data Check)
                is_valid_logic, error_msg_logic = GameEngine.validate_move(
                    board=game["board"],
                    position=position,
                    current_turn_player_id=game["current_turn"],
                    requesting_player_id=user_id
                )
                
                if not is_valid_logic:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": error_msg_logic
                    }, websocket)
                    continue

                # Validate Guess (Content Check)
                is_valid_guess = GameEngine.validate_guess(player_doc, row_criteria, col_criteria)
                
                if not is_valid_guess:
                     await manager.send_personal_message({
                        "type": "error",
                        "message": f"Player '{player_doc['player_name']}' does not match {row_criteria} and {col_criteria}."
                    }, websocket)
                     continue
                
                if not is_valid_guess:
                     await manager.send_personal_message({
                        "type": "error",
                        "message": f"Player '{player_doc['player_name']}' does not match {row_criteria} and {col_criteria}."
                    }, websocket)
                     continue
                
                # Determine symbol
                symbol = "X" if user_id == game["player1_id"] else "O"
                
                # Apply Move
                new_board = GameEngine.make_move(game["board"], position, symbol)
                
                # Check Winner
                winner_symbol = GameEngine.check_winner(new_board)
                
                # Calculate next state
                next_turn = game["player2_id"] if user_id == game["player1_id"] else game["player1_id"]
                
                update_data = {
                    "board": new_board,
                    "current_turn": next_turn,
                    "updated_at": datetime.utcnow()
                }
                
                winner_id = None
                if winner_symbol:
                    update_data["status"] = "completed"
                    if winner_symbol == "draw":
                        winner_id = "draw"
                    else:
                        winner_id = user_id if winner_symbol == symbol else next_turn
                    
                    update_data["winner"] = winner_id

                    # Update User Stats
                    if winner_id == "draw":
                        await users_collection.update_many(
                            {"user_id": {"$in": [game["player1_id"], game["player2_id"]]}},
                            {"$inc": {"draws": 1, "total_games": 1}}
                        )
                    elif winner_id:
                        # Winner
                        await users_collection.update_one(
                            {"user_id": winner_id},
                            {"$inc": {"wins": 1, "total_games": 1}}
                        )
                        # Loser
                        loser_id = game["player2_id"] if winner_id == game["player1_id"] else game["player1_id"]
                        await users_collection.update_one(
                            {"user_id": loser_id},
                            {"$inc": {"losses": 1, "total_games": 1}}
                        )
                
                # Persist
                await games_collection.update_one(
                    {"game_id": game_id},
                    {"$set": update_data}
                )
                
                # Broadcast
                await manager.broadcast_to_game({
                    "type": "move_made",
                    "user_id": user_id,
                    "position": position,
                    "symbol": symbol,
                    "board": new_board,
                    "next_turn": next_turn if not winner_symbol else None,
                    "winner": winner_id,
                    "game_status": update_data.get("status", "in_progress"),
                    "timestamp": datetime.utcnow().isoformat()
                }, game_id)
            
            elif data["type"] == "chat":
                await manager.broadcast_to_game({
                    "type": "chat_message",
                    "user_id": user_id,
                    "username": user["username"],
                    "message": data["message"],
                    "timestamp": datetime.utcnow().isoformat()
                }, game_id)
    
    except WebSocketDisconnect:
        manager.disconnect(game_id, user_id)
        await manager.broadcast_to_game({
            "type": "player_disconnected",
            "user_id": user_id,
            "username": user["username"],
            "timestamp": datetime.utcnow().isoformat()
        }, game_id)