import pandas as pd
import re
import math

def process_tournament_data(file_path):
    try:
        df = pd.read_excel(file_path, header=None)
    except Exception as e:
        print(f"Error loading file: {e}")
        return None

    # New categories as requested
    categories = {
        "Junior Total": {},
        "Adult Singles": {},
        "Adult Doubles": {},
        "Adult Mixed": {}
    }
    
    current_section = None
    is_main_draw = False
    active_cat = None

    for _, row in df.iterrows():
        col_a = str(row[0]).strip()
        # Using row[2] as per your working version
        player_name = str(row[2]).strip() 
        club_name = str(row[3]).strip()

        if col_a != "nan" and col_a != "":
            current_section = col_a
            is_main_draw = current_section.endswith("Main Draw")
            
            if is_main_draw:
                is_junior = bool(re.search(r'U\d+', current_section))
                
                if is_junior:
                    active_cat = "Junior Total"
                else:
                    # Adult Logic: Determine specific discipline
                    parts = current_section.replace("Entries of ", "").split()
                    code = parts[0].upper() if parts else ""
                    
                    if len(code) >= 2:
                        char_1 = code[0]
                        char_2 = code[1]
                        if char_2 == 'S':
                            active_cat = "Adult Singles"
                        elif char_1 == "X" and char_2 == 'D':
                            active_cat = "Adult Mixed"
                        elif char_2 == 'D':
                            active_cat = "Adult Doubles"
                        else:
                            print("❌  ERROR, a class does not fit any adult chategory!!")
                            active_cat = None # Fallback for codes like "W3" etc
                    else:
                        active_cat = None
            continue
        
        if is_main_draw and active_cat:
            if player_name in ["nan", "None", "Name", ""] or club_name in ["Club", "nan"]:
                continue

            if active_cat != "Junior Total":
                player_name = f"{player_name} ({current_section})"
            categories[active_cat][player_name] = club_name

    return categories

def print_full_category_report(categories):
    print(f"\n{'#'*85}")
    print(f"{'FULL TOURNAMENT PLAYER LIST':^85}")
    print(f"{'#'*85}")

    for cat_name, player_data in categories.items():
        if not player_data:
            continue
            
        print(f"\n[ {cat_name.upper()} ]")
        print(f"{'-'*85}")
        print(f"{'Player Name':<45} | {'Club':<35}")
        print(f"{'-'*85}")
        
        for player in sorted(player_data.keys()):
            print(f"{player:<45} | {player_data[player]:<35}")
        print(f"Total Category Size: {len(player_data)} unique players")


def analyze_club_participation(categories, target_club):
    # Width calculation: slightly wider to handle three math strings in one row
    total_width = 130
    
    print("\n" + "=" * total_width)
    print(f" CLUB ANALYSIS: {target_club.upper()} ")
    print("=" * total_width)
    
    # Headers - Adjusted widths for the longer math strings
    print(f"{'Category':<28} | {'Players/Pairs from club':<25} | {'Players/Pairs from other clubs':<30} | {'Total player/pair amount in category':<35}")
    print("-" * total_width)

    all_players_unique = {}

    for cat_name, player_data in categories.items():
        all_players_unique.update(player_data)
        
        # 1. Calculate raw counts
        total_count = len(player_data)
        club_count = sum(1 for club in player_data.values() if club == target_club)
        other_count = total_count - club_count
        
        # 2. Check if we should apply the "Doubles/Mixed" math formatting
        if "Doubles" in cat_name or "Mixed" in cat_name:
            # Helper to format: "X / 2 = Y" (rounded up)
            devide_round_up = lambda x: f"{x} / 2 = {math.ceil(x / 2)}"
            devide_round_down = lambda x: f"{x} / 2 = {math.floor(x / 2)}"
            devide = lambda x: f"{x} / 2 = {int(x / 2)}"
            
            display_club = devide_round_up(club_count)
            display_other = devide_round_down(other_count)
            display_total = devide(total_count)
        else:
            # For Singles or Junior Total, keep as plain strings
            display_club = str(club_count)
            display_other = str(other_count)
            display_total = str(total_count)
        
        # 3. Print the row using the display variables
        print(f"{cat_name:<28} | {display_club:<25} | {display_other:<30} | {display_total:<30}")

    # Totals Section (Unique players - usually stays as raw numbers as players 
    # might play both Singles and Doubles, making a division here misleading)
    total_club_unique = sum(1 for club in all_players_unique.values() if club == target_club)
    total_tourney_unique = len(all_players_unique)
    total_others_unique = total_tourney_unique - total_club_unique
    
    print("-" * total_width)
    print(f"{'TOTAL UNIQUE PLAYER AMOUNTS':<28} | {total_club_unique:<25} | {total_others_unique:<30} | {total_tourney_unique:<30}")
    print("=" * total_width)

if __name__ == "__main__":
    file_path = 'tävlingsraport Junnutävling 2026.xlsx'
    player_cats = process_tournament_data(file_path)

    if player_cats:
        #print_full_category_report(player_cats)
        target = "Helsingfors Badminton Club" 
        analyze_club_participation(player_cats, target)


        