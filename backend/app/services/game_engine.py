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

    @staticmethod
    def generate_grid_headers(ipl_teams: List[str], national_teams: List[str]) -> dict:
        """
        Randomly assigns 3 teams for rows and 3 teams for columns.
        Constraints:
        1. Max 2 nations in a game.
        2. Nations must be on 1 axis only (either horizontal or vertical).
        """
        import random
        
        # Decide which axis gets the nations
        nation_axis = random.choice(['rows', 'cols'])
        other_axis = 'cols' if nation_axis == 'rows' else 'rows'
        
        # Shuffle inputs to ensure randomness
        random.shuffle(ipl_teams)
        random.shuffle(national_teams)
        
        # Select up to 2 nations
        selected_nations = national_teams[:2]
        
        # We need 3 headers for each axis.
        # The nation axis will have the nations + some IPL teams.
        # The other axis will have only IPL teams.
        
        nation_axis_headers = selected_nations + ipl_teams[:(3 - len(selected_nations))]
        random.shuffle(nation_axis_headers)
        
        other_axis_headers = ipl_teams[(3 - len(selected_nations)):(6 - len(selected_nations))]
        random.shuffle(other_axis_headers)
        
        return {
            nation_axis: nation_axis_headers,
            other_axis: other_axis_headers
        }

    @staticmethod
    def validate_guess(player_data: dict, row_criteria: str, col_criteria: str) -> bool:
        """
        Validates if the guessed player matches the criteria for the chosen cell.
        The player must match EITHER the row criteria (IPL Team/Country) 
        OR the column criteria. 
        
        Wait, standard Tic Tac Toe with Cricket players usually means the player 
        must contain attributes of BOTH the row and column. 
        
        Example: Row=CSK, Col=India. Player must be MS Dhoni (played for CSK AND India).
        """
        player_teams = player_data.get("IPL Teams", [])
        player_country = player_data.get("Country")
        
        # Normalize criteria for comparison
        # (Assuming data in DB is consistent, but good to be safe)
        
        matches_row = (row_criteria in player_teams) or (row_criteria == player_country)
        matches_col = (col_criteria in player_teams) or (col_criteria == player_country)
        
        return matches_row and matches_col
