
# THIS FILE HOLDS THE RELEVANT INFORMATION ABOUT THE COMPETITION
from pathlib import Path
current_dir = Path(__file__).parent

# the excel (remember .xlsx)
#file_path = "Junnu entries.xlsx"
#file_path = "Entries Dubbelturnering 2026 1.1.xlsx"
#file_path = "Entries HBC Premier Elite 2024.xlsx"
file_path = current_dir / "Helsinki Open Elit 2026" / "Official Entries Helsinki Open Elit 2026 copy.xlsx"

# the model
model = "model_elite.mzn"

# pool or elimination
pool = False


# days, times of days, and courts
friday = []
saturday = ["09:00", "21:00", 16]
sunday = [
    ["9:00", "14:00", 12],
    ["14:15", "19:30", 6]
]

# upmire chairs
umpire_chairs = 5

# Strong collision time gap
4
# Weak collision time gap
3
# Super weak collision time gap
2

# V between rounds gap
6
# A between rounds gap
5
# Rest between rounds gap
5
# Junior between rounds gap

# The amount of matches in an umpire round needed to get tighter time constraints for the starttime of the matches
a = 4 # this number should be <= umpire_chairs
# Max umprire round duration (if there are > a mathces in the round)
1
# Max umprire round duration (if there are <= a mathces in the round)
3

# The amount of matches in a non-umpire round needed to get tighter time constraints for the starttime of the matches
b = 8 # this number needs be <= max fields
# Max non-umpite round duration (if there are > b mathces in the round)
1
# Max non-umpite round duration (if there are <= b mathces in the round)
3

# Umpire match duration
3
# Non-upire match duration
2

# The amount of rounds in a class needed to get tighter time constraints for the class
c = 3
# In classes with > c rounds: all matches within (rounds * x) timeslots
x = 20
# In classes with <= c rounds: all matches within (rounds * y) timeslots
y = 10




# Pretty print
def print_competition_info():
    # --- Configuration Summary Printout ---
    print("")
    print("="*50)
    print(f"{'TOURNAMENT CONFIGURATION':^50}")
    print("="*50)

    # 1. File & Method
    print(f"📁 Competition Excel : {file_path}")
    print(f"🏆 Method of Play    : {'Pool' if pool else 'Elimination'}")
    print("-" * 50)

    # 2. Days and Times Summary
    print("📅 Competition Schedule:")

    # Helper to print day status
    def print_day(name, day_config):
        if not day_config:
            print(f"  ❌ {name:<8}: Not scheduled")
            return
        
        # Normalize: if it's a single flat list like ["09:00", "20:00", 16], wrap it in a list
        if isinstance(day_config[0], str):
            blocks = [day_config]
        else:
            blocks = day_config

        # Print formatting
        if len(blocks) == 1:
            start, end, courts = blocks[0]
            print(f"  ✅ {name:<8}: {start:>5} to {end:>5} ({courts:>2} courts)")
        else:
            print(f"  ✅ {name:<8}:")
            for i, block in enumerate(blocks):
                start, end, courts = block[0], block[1], block[2]
                print(f"      └─ Block {i+1}: {start:>5} to {end:>5} ({courts:>2} courts)")

    print_day("Friday", friday)
    print_day("Saturday", saturday)
    print_day("Sunday P1", sunday)

    print("="*50)
    print("")

print_competition_info()