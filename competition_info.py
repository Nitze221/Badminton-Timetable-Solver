
# THIS FILE HOLDS THE RELEVANT INFORMATION ABOUT THE COMPETITION

# the excel (remember .xlsx)
#file_path = "Junnu entries.xlsx"
#file_path = "Entries Dubbelturnering 2026 1.1.xlsx"
file_path = "Entries HBC Premier Elite 2024.xlsx"

# the model
model = "model_elite.mzn"

# pool or elimination
pool = False


# days, times of days, and courts
friday = []
saturday = ["09:00", "20:00", 16]
sunday = [
    ["9:00", "12:00", 12],
    ["12:15", "16:30", 6]
]

# upmire chairs
umpire_chairs = 4

'''

# days
friday = False
saturday = True
sunday_1 = True
sunday_2 = True
sunday_3 = False

# times of days
friday_start_time = "18:00"
friday_end_time = "21:00"

saturday_start_time = "09:00"
saturday_end_time = "21:00"

sunday_start_time_1 = "09:00"
sunday_end_time_1 = "12:00"

sunday_start_time_2 = "12:00"
sunday_end_time_2 = "17:30"

sunday_start_time_3 = "14:30"
sunday_end_time_3 = "19:00"

# courts
friday_saturday_sunday_1_courts = 12
sunday_courts_2 = 8
sunday_courts_3 = 6
'''




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