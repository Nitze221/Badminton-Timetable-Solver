
# THIS FILE HOLDS THE RELEVANT INFORMATION ABOUT THE COMPETITION

# the excel (remember .xlsx)
#file_path = "Junnu entries.xlsx"
#file_path = "Entries Dubbelturnering 2026 1.1.xlsx"
file_path = "Entries HBC Premier Elite 2024.xlsx"

# the model
model = "model_elite.mzn"

# pool or elimination
pool = False

# days
friday = False
saturday = True
sunday_1 = True
sunday_2 = True
sunday_3 = False

#friday = False
#saturday = True
#sunday = True

# times of days and courts
#friday = []
#saturday = ["09:00", "20:00", 16]
#sunday = [["9:00", "12:00", 12], ["12:00", "16:30", 6]]

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
    def print_day(name, active, start, end, courts):
        status = "✅" if active else "❌"
        if active:
            print(f"  {status} {name:<10}: {start} to {end} ({courts} courts)")
        else:
            print(f"  {status} {name:<10}: Not scheduled")

    print_day("Friday", friday, friday_start_time, friday_end_time, friday_saturday_sunday_1_courts)
    print_day("Saturday", saturday, saturday_start_time, saturday_end_time, friday_saturday_sunday_1_courts)
    print_day("Sunday P1", sunday_1, sunday_start_time_1, sunday_end_time_1, friday_saturday_sunday_1_courts)
    print_day("Sunday P2", sunday_2, sunday_start_time_2, sunday_end_time_2, sunday_courts_2)
    print_day("Sunday P3", sunday_3, sunday_start_time_3, sunday_end_time_3, sunday_courts_3)

    print("="*50)
    print("")

print_competition_info()