
import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.game_engine import GameEngine

def test_generation():
    ipl_teams = ["CSK", "MI", "RCB", "KRR", "GT", "LSG"]
    national_teams = ["India", "Australia", "England", "South Africa"]
    
    print("Testing generate_grid_headers...")
    
    for i in range(10):
        headers = GameEngine.generate_grid_headers(ipl_teams, national_teams)
        
        rows = headers['rows']
        cols = headers['cols']
        
        all_headers = rows + cols
        nations_in_game = [h for h in all_headers if h in national_teams]
        
        nations_in_rows = [h for h in rows if h in national_teams]
        nations_in_cols = [h for h in cols if h in national_teams]
        
        print(f"Run {i+1}:")
        print(f"  Rows: {rows}")
        print(f"  Cols: {cols}")
        print(f"  Nations count: {len(nations_in_game)}")
        print(f"  Nation Axis: {'rows' if nations_in_rows else 'cols' if nations_in_cols else 'none'}")
        
        # Assertions
        assert len(nations_in_game) <= 2, f"Too many nations: {nations_in_game}"
        assert not (nations_in_rows and nations_in_cols), "Nations on both axes!"
        assert len(set(all_headers)) == 6, f"Duplicate headers: {all_headers}"
        
    print("\nAll tests passed!")

if __name__ == "__main__":
    test_generation()
