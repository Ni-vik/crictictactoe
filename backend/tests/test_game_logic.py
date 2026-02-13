import pytest
from app.services.game_engine import GameEngine

class TestGameEngine:
    def test_check_winner_rows(self):
        # Row 1
        board = ["X", "X", "X", "", "", "", "", "", ""]
        assert GameEngine.check_winner(board) == "X"
        
        # Row 2
        board = ["", "", "", "O", "O", "O", "", "", ""]
        assert GameEngine.check_winner(board) == "O"

    def test_check_winner_cols(self):
        # Col 1
        board = ["X", "", "", "X", "", "", "X", "", ""]
        assert GameEngine.check_winner(board) == "X"

    def test_check_winner_diagonals(self):
        # Diag 1
        board = ["X", "", "", "", "X", "", "", "", "X"]
        assert GameEngine.check_winner(board) == "X"
        
        # Diag 2
        board = ["", "", "O", "", "O", "", "O", "", ""]
        assert GameEngine.check_winner(board) == "O"

    def test_check_winner_draw(self):
        board = ["X", "O", "X", "X", "O", "O", "O", "X", "X"]
        assert GameEngine.check_winner(board) == "draw"

    def test_check_winner_none(self):
        board = ["X", "O", "", "", "", "", "", "", ""]
        assert GameEngine.check_winner(board) is None

    def test_validate_move_success(self):
        board = [""] * 9
        is_valid, msg = GameEngine.validate_move(board, 0, "p1", "p1")
        assert is_valid is True
        assert msg is None

    def test_validate_move_wrong_turn(self):
        board = [""] * 9
        is_valid, msg = GameEngine.validate_move(board, 0, "p1", "p2")
        assert is_valid is False
        assert msg == "Not your turn"

    def test_validate_move_position_taken(self):
        board = ["X"] + [""] * 8
        is_valid, msg = GameEngine.validate_move(board, 0, "p2", "p2")
        assert is_valid is False
        assert msg == "Position already taken"

    def test_validate_move_out_of_bounds(self):
        board = [""] * 9
        is_valid, msg = GameEngine.validate_move(board, 9, "p1", "p1")
        assert is_valid is False
        assert msg == "Invalid position"

    def test_make_move(self):
        board = [""] * 9
        new_board = GameEngine.make_move(board, 0, "X")
        assert new_board[0] == "X"
        assert board[0] == ""  # Ensure immutability/copy if intended (list is mutable, but function should return new state or update)
        
        # NOTE: Current implementation returns a new list
