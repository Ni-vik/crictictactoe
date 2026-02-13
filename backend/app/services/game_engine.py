from typing import List, Optional, Tuple

class GameEngine:
    @staticmethod
    def check_winner(board: List[str]) -> Optional[str]:
        """Check if there's a winner. Returns 'X', 'O', 'draw', or None"""
        # Winning combinations
        wins = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]              # Diagonals
        ]
        
        for combo in wins:
            if board[combo[0]] and board[combo[0]] == board[combo[1]] == board[combo[2]]:
                return board[combo[0]]
        
        # Check for draw
        if "" not in board:
            return "draw"
        
        return None

    @staticmethod
    def validate_move(board: List[str], position: int, current_turn_player_id: str, requesting_player_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validates a move.
        Returns: (is_valid, error_message)
        """
        if current_turn_player_id != requesting_player_id:
            return False, "Not your turn"
        
        if not (0 <= position < 9):
            return False, "Invalid position"
            
        if board[position] != "":
            return False, "Position already taken"
            
        return True, None

    @staticmethod
    def make_move(board: List[str], position: int, player_symbol: str) -> List[str]:
        """
        Applies a move to the board. Assumes validation has passed.
        Returns the new board state.
        """
        new_board = list(board)
        new_board[position] = player_symbol
        return new_board
