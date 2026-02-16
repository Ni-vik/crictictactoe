
import asyncio
import os
import sys
from collections import defaultdict
from itertools import combinations, product

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from database.db import players_collection

async def main():
    print("Fetching players...")
    players = await players_collection.find().to_list(length=None)
    print(f"Total players found: {len(players)}")

    if not players:
        print("No players found in database.")
        return

    # 1. Analyze Teams and Countries
    all_ipl_teams = set()
    all_countries = set()
    
    # Store player counts for each criteria
    criteria_counts = defaultdict(int) 
    
    # Store players for each criteria to easily check intersections
    players_by_criteria = defaultdict(set)

    for p in players:
        pid = str(p.get('_id'))
        
        # IPL Teams
        teams = p.get('IPL Teams', [])
        if isinstance(teams, str):
            teams = [teams] # Handle string case if any
            
        for team in teams:
            all_ipl_teams.add(team)
            criteria_counts[team] += 1
            players_by_criteria[team].add(pid)
            
        # Country
        country = p.get('Country')
        if country:
            all_countries.add(country)
            criteria_counts[country] += 1
            players_by_criteria[country].add(pid)

    print(f"\nUnique IPL Teams ({len(all_ipl_teams)}): {sorted(list(all_ipl_teams))}")
    print(f"Unique Countries ({len(all_countries)}): {sorted(list(all_countries))}")

    # 2. Check Intersections (Grid Cells)
    # A cell defined by (Row, Col) is valid if there is at least one player 
    # who satisfies BOTH criteria.
    # Player P matches Rule X if X in P.Teams OR X == P.Country.

    # Let's check Country vs Country specific constraint
    print("\n--- Verifying Country vs Country Intersections ---")
    print("Constraint: 'One player cannot be from Australia and England'")
    
    country_pairs = list(combinations(all_countries, 2))
    valid_country_pairs = []
    
    for c1, c2 in country_pairs:
        # Intersection: players who match c1 AND match c2
        # Since a player has only ONE country, they can match both ONLY if
        # one of the countries is listed in their IPL Teams (impossible)
        # OR if they have multiple countries (unlikely).
        
        # Intersection of sets
        common_players = players_by_criteria[c1].intersection(players_by_criteria[c2])
        
        if common_players:
            print(f"WARNING: Found players for {c1} AND {c2}: {len(common_players)}")
            valid_country_pairs.append((c1, c2))
        else:
            # This is expected for Country vs Country
            pass

    if not valid_country_pairs:
        print("CONFIRMED: No players satisfy two different countries simultaneously.")
        print("Therefore, we CANNOT have different Country headers on intersecting Row and Column.")
    
    # 3. Verify 'Nations on 1 axis only' logic
    print("\n--- Testing constraints: Max 2 Nations, Same Axis ---")
    
    # Let's simulate generating random grids with these constraints and see if we find valid players.
    
    # Constraint Parameters:
    # - Rows: 3 headers
    # - Cols: 3 headers
    # - Total Nations <= 2
    # - Nations on EITHER Rows OR Cols (XOR)
    
    # Strategy:
    # 1. Pick Axis for Nations (Rows or Cols). Let's say Rows have nations.
    # 2. Pick 0, 1, or 2 Nations for Rows. Fill rest of Rows with IPL Teams.
    # 3. Cols must be ALL IPL Teams (since nations are on Rows).
    # 4. OR: No nations at all (0 nations).
    
    # We need to verify if there exist valid grids under these constraints.
    # A valid grid means EVERY cell (r, c) has >= 1 player.
    
    valid_grids_found = 0
    samples_to_check = 1000
    
    import random
    
    print(f"Simulating {samples_to_check} random grids with constraints...")
    
    for i in range(samples_to_check):
        # 1. Decide if we use nations
        use_nations = random.choice([True, False])
        nations_count = 0
        nation_axis = 'none'
        
        row_headers = []
        col_headers = []
        
        available_nations = list(all_countries)
        available_teams = list(all_ipl_teams)
        
        if use_nations:
            nations_count = random.randint(1, 2) # Limit to 2
            nation_axis = random.choice(['row', 'col'])
            
            selected_nations = random.sample(available_nations, min(nations_count, len(available_nations)))
            
            if nation_axis == 'row':
                # Fill rows with selected nations + random teams
                needed_teams_row = 3 - len(selected_nations)
                row_headers = selected_nations + random.sample(available_teams, needed_teams_row)
                # Cols must be teams only
                # Ensure no overlap in teams if desired, or allow overlap? Assuming distinct headers.
                remaining_teams = [t for t in available_teams if t not in row_headers] # remove used teams?
                # Actually headers should be distinct across the board usually
                col_headers = random.sample(remaining_teams, 3)
                
            else: # col
                # Fill cols with selected nations + random teams
                needed_teams_col = 3 - len(selected_nations)
                col_headers = selected_nations + random.sample(available_teams, needed_teams_col)
                # Rows must be teams only
                remaining_teams = [t for t in available_teams if t not in col_headers]
                row_headers = random.sample(remaining_teams, 3)
                
        else:
            # No nations, all teams
            all_t = random.sample(available_teams, 6)
            row_headers = all_t[:3]
            col_headers = all_t[3:]
            
        # Verify Grid
        is_grid_valid = True
        min_options = 999
        
        for r in row_headers:
            for c in col_headers:
                # Check intersection
                intersection = players_by_criteria[r].intersection(players_by_criteria[c])
                if not intersection:
                    is_grid_valid = False
                    break
                min_options = min(min_options, len(intersection))
            if not is_grid_valid:
                break
        
        if is_grid_valid:
            valid_grids_found += 1
            if valid_grids_found == 1:
                print(f"Sample Valid Grid:")
                print(f"  Rows: {row_headers}")
                print(f"  Cols: {col_headers}")
                print(f"  Min players per cell: {min_options}")
                
    print(f"\nValid Grids Found: {valid_grids_found}/{samples_to_check} ({valid_grids_found/samples_to_check*100:.1f}%)")
    
    if valid_grids_found == 0:
        print("CRITICAL: No valid grids found with current constraints and data!")
    else:
        print("Success: Valid grids are possible under these constraints.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
