import minizinc
import asyncio
from parse_excel import minizinc_data


from openpyxl import load_workbook, Workbook
from openpyxl.styles import PatternFill

from datetime import datetime, timedelta

def find_class(match_index, class_index):
    # Find which class a match belongs to
    class_id = 0
    for i, start in enumerate(class_index):
        if i + 1 < len(class_index):
            if start <= match_index < class_index[i + 1]:
                class_id = i + 1
                break
        else:
            # Last class
            if start <= match_index:
                class_id = i + 1
                break
    return class_id

def find_round(match_index, class_index, round_index):
    """
    Determine round number relative to the match's class.
    Rounds reset when a new class starts.
    """
    class_id = find_class(match_index, class_index)
    class_start = class_index[class_id-1]
    next_class_start = class_index[class_id] if class_id < len(class_index) else float("inf")

    # Count how many round starts are within this class before or at match_index
    local_rounds = [r for r in round_index if class_start <= r < next_class_start and r <= match_index]

    round_id = len(local_rounds)  # round numbering starts at 0
    return round_id


def build_schedule(class_index, round_index, time_of_match, class_names, data):
    # Find how many time slots exist
    num_groups = data["timeslots_12_fields"] + data["timeslots_8_fields"] + data["timeslots_6_fields"]  # assuming time slots start at 0

    # Initialize 2D list of None values (each slot has 10 possible matches)
    schedule = [["        " for _ in range(data["fields_1"])] for _ in range(num_groups)]

    # Track how many matches are already in each time slot
    slot_counts = [0] * num_groups

    # Go through each match
    for match_index, time_slot in enumerate(time_of_match):
        # Find current count for this slot
        # group_slot = (time_slot - 1) // data["fields"]  # group every 10 slots together
        count = slot_counts[time_slot-1]
        
        match_index_plus_one = match_index + 1     # since matches index starts with 1
        # Only place if there’s still space
        if count < data["fields_1"]:
            class_id = find_class(match_index_plus_one, class_index)
            round_id = find_round(match_index_plus_one, class_index, round_index)
            schedule[time_slot-1][count] = f"{class_names[class_id - 1]} - {round_id}"
            slot_counts[time_slot-1] += 1
        else:
            # Optional: warn if slot overflows
            print(f"Warning: time slot {time_slot-1} already full")

    return schedule

def write_schedule_to_excel(file_path, schedule, colors, sheet_name="timetable", start_row=2, start_col=2):
    """
    Writes the schedule to an Excel sheet with row numbers (1-12) 
    and time headers (starting at 09:00).
    """
    # Load workbook or create new
    try:
        book = load_workbook(file_path)
    except FileNotFoundError:
        book = Workbook()

    # Create or overwrite sheet
    if sheet_name in book.sheetnames:
        sheet = book[sheet_name]
        book.remove(sheet)
    
    sheet = book.create_sheet(sheet_name)

    # 1. Write Row Numbers (1-12) in the column to the left
    for i in range(12):
        sheet.cell(row=start_row + i, column=start_col - 1).value = i + 1

    # 2. Write Time Headers (9:00, 9:15, etc.) in the row above
    current_time = datetime.strptime("09:00", "%H:%M")
    for col_idx in range(len(schedule)):
        time_str = current_time.strftime("%H:%M")
        sheet.cell(row=start_row - 1, column=start_col + col_idx).value = time_str
        current_time += timedelta(minutes=15)

    # Mapping class prefix -> color
    class_color_map = {
        key: PatternFill(start_color=value, end_color=value, fill_type="solid")
        for key, value in colors.items()
    }

    # 3. Write the schedule
    for col_idx, time_slot in enumerate(schedule, start=start_col):
        for row_idx, match in enumerate(time_slot, start=start_row):
            if match == "        " or not match:
                continue

            cell = sheet.cell(row=row_idx, column=col_idx)
            cell.value = match

            # Determine class prefix
            match_clean = str(match).strip()
            words = match_clean.split()
            if len(words) >= 2:
                class_prefix = " ".join(words[:2])
                
                if class_prefix in class_color_map:
                    cell.fill = class_color_map[class_prefix]

    # Save workbook
    book.save(file_path)


'''
colors = {
    # Blues
    "MS V" : "E3F2FD", "WS V" : "BBDEFB", "MD V" : "90CAF9", "WD V" : "64B5F6", "XD V" : "42A5F5",
    # Greens
    "MS A" : "E8F5E9", "WS A" : "C8E6C9", "MD A" : "A5D6A7", "WD A" : "81C784", "XD A" : "66BB6A",
    # Reds/Pinks
    "MS B" : "FDE0E0", "WS B" : "F8BBD0", "MD B" : "F48FB1", "WD B" : "F06292", "XD B" : "EC407A",
    # Yellows/Oranges
    "MS C" : "FFF8E1", "WS C" : "FFECB3", "MD C" : "FFE082", "WD C" : "FFD54F", "XD C" : "FFCA28"
}

class_names = [
        "MS V", "WS V", "MD V", "WD V", "XD V",
        "MS A", "WS A", "MD A", "WD A", "XD A",
        "MS B", "WS B", "MD B", "WD B", "XD B",
        "MS C", "WS C", "MD C", "WD C", "XD C"
    ]

colors = {
    # Juniors U11 - U13 (Light Purples/Indigos)
    "BS U11": "F3E5F5", 
    "BS U13": "E1BEE7", "GS U13": "D1C4E9", "XD U13": "E1BEE7", "BD U13": "B39DDB",
    
    # Juniors U15 (Teals)
    "BS U15": "E0F2F1", "GS U15": "B2DFDB", "BD U15": "4DB6AC",
    # Note: Added these back in case you need them later, though not in your current list
    "XD U15": "80CBC4", "GD U15": "26A69A",
    
    # Juniors U17 (Light Blues)
    "BS U17": "E1F5FE", "GS U17": "B3E5FC", "XD U17": "81D4FA", "BD U17": "4FC3F7", "GD U17": "29B6F6",
    
    # Seniors 40 - 55 (Greens)
    "MD 40": "E8F5E9", "MD 45": "C8E6C9", "XD 45": "C8E6C9", 
    "MD 50": "A5D6A7", "MD 55": "81C784", "XD 55": "81C784",
    
    # Seniors 60 - 70 (Amber/Orange)
    "MD 60": "FFF8E1", "XD 60": "FFECB3", "MD 65": "FFE082", "MD 70": "FFCA28",

    # Elite/Open Class V & A (Blues)
    "MD V": "E3F2FD", "WD V": "BBDEFB", "XD V": "BBDEFB", 
    "MD A": "90CAF9", "WD A": "64B5F6", "XD A": "42A5F5",

    # Class B & C (Reds/Pinks)
    "MD B": "FCE4EC", "WD B": "F8BBD0", "XD B": "F48FB1", 
    "MD C": "FDE0E0", "WD C": "F06292", "XD C": "EC407A"
}
'''
'''
class_names = [
    "BS U11", "BS U13", "GS U13", "XD U13", "BD U13", 
    "BS U15", "GS U15", "BD U15",
    "BS U17", "GS U17", "XD U17", "BD U17", "GD U17", 
    "MD 40", "MD 45", "XD 45", "MD 50", "MD 55", "XD 55",
    "MD 60", "XD 60", "MD 65", "MD 70",
    "MD V", "WD V", "XD V", "MD A", "WD A", "XD A",
    "MD B", "WD B", "XD B", "MD C", "WD C", "XD C"
]
'''
class_names = [
    "BS U11", "GS U11", "BD U11", 
    "BS U13", "GS U13", "XD U13", "BD U13", 
    "BS U15", "GS U15", "BD U15", "GD U15",
    "BS U17", "GS U17", "XD U17", "BD U17"
]

colors = {
    # Juniors U11 (Light Purples/Indigos)
    "BS U11": "F3E5F5", "GS U11": "D1C4E9", "BD U11": "E1BEE7",
    
    # Juniors U13 (Light Blues)
    "BS U13": "E1F5FE", "GS U13": "B3E5FC", "XD U13": "81D4FA", "BD U13": "4FC3F7",
    
    # Juniors U15 (Greens)
    "BS U15": "E8F5E9", "GS U15": "C8E6C9", "BD U15": "C8E6C9", "GD U15": "A5D6A7",

    # Juniors U17 (Blues)
    "BS U17": "E3F2FD", "GS U17": "BBDEFB", "XD U17": "BBDEFB", "BD U17": "90CAF9"

}





async def main():
    # Load model
    model = minizinc.Model("model_tof.mzn")

    data = minizinc_data()



    # Choose solver (you can replace "gecode" with another installed solver)
    solver = minizinc.Solver.lookup("chuffed")
    #solver = minizinc.Solver.lookup("gecode")

    # Create instance and give input
    '''
    instance = minizinc.Instance(solver, model)
    instance["nof_matches"] = len(data["matches"])
    instance["nof_umpire_matches"] = len(data["umpire_matches"])
    instance["nof_matches_no_umpire"] = len(data["matches_no_umpire"])

    instance["nof_classes"] = len(data["class_index"])
    instance["nof_rounds"] = len(data["round_index"])
    instance["nof_strong_collisions"] = len(data["strong_collision"])
    instance["nof_weak_collisions"] = len(data["weak_collision"])
    instance["nof_super_weak_collisions"] = len(data["super_weak_collision"])
    instance["nof_elit_rounds"] = data["nof_elit_rounds"]
    instance["nof_elit_classes"] = data["nof_elit_classes"]

    instance["class_index"] = data["class_index"]
    instance["round_index"] = data["round_index"]
    instance["umpire_matches"] = data["umpire_matches"]
    instance["matches_no_umpire"] = data["matches_no_umpire"]

    instance["timeslots"] = data["timeslots"]
    instance["fields"] = data["fields"]
    instance["matchslots"] = data["matchslots"]

    instance["strong_collision"] = data["strong_collision"]
    instance["weak_collision"] = data["weak_collision"]
    instance["super_weak_collision"] = data["super_weak_collision"]
    instance["last_of_day1"] = data["last_of_day1"]
    instance["last_of_day0"] = data["last_of_day0"]
    '''
    instance = minizinc.Instance(solver, model)

    instance["strong_collision"] = data["strong_collision"]
    instance["weak_collision"] = data["weak_collision"]
    instance["super_weak_collision"] = data["super_weak_collision"]

    instance["nof_strong_collisions"] = len(data["strong_collision"])
    instance["nof_weak_collisions"] = len(data["weak_collision"])
    instance["nof_super_weak_collisions"] = len(data["super_weak_collision"])


    instance["class_index"] = data["class_index"]
    instance["round_index"] = data["round_index"]

    instance["nof_classes"] = len(data["class_index"])
    instance["nof_rounds"] = len(data["round_index"])


    instance["timeslots_12_fields"] = data["timeslots_12_fields"]
    instance["timeslots_8_fields"] = data["timeslots_8_fields"]
    instance["timeslots_6_fields"] = data["timeslots_6_fields"]


    instance["fields_1"] = data["fields_1"]
    instance["fields_2"] = data["fields_2"]
    instance["fields_3"] = data["fields_3"]


    instance["matchslots_1"] = data["matchslots_1"]
    instance["matchslots_2"] = data["matchslots_2"]
    instance["matchslots_3"] = data["matchslots_3"]


    instance["last_of_day1"] = data["last_of_day1"]
    instance["last_of_day0"] = data["last_of_day0"]


    instance["nof_V_classes"] = data["nof_V_classes"]
    instance["nof_A_classes"] = data["nof_A_classes"]
    instance["nof_junior_classes"] = data["nof_junior_classes"]

    instance["V_start"] = data["V_start"]
    instance["V_end"] = data["V_end"]
    instance["A_start"] = data["A_start"]
    instance["A_end"] = data["A_end"]
    instance["junior_start"] = data["junior_start"]
    instance["junior_end"] = data["junior_end"]


    instance["nof_V_rounds"] = data["nof_V_rounds"]
    instance["nof_A_rounds"] = data["nof_A_rounds"]
    instance["nof_junior_rounds"] = data["nof_junior_rounds"]

    instance["V_rounds_start"] = data["V_rounds_start"]
    instance["V_rounds_end"] = data["V_rounds_end"]
    instance["A_rounds_start"] = data["A_rounds_start"]
    instance["A_rounds_end"] = data["A_rounds_end"]
    instance["junior_rounds_start"] = data["junior_rounds_start"]
    instance["junior_rounds_end"] = data["junior_rounds_end"]


    instance["all_matches"] = data["matches"]
    instance["V_matches"] = data["V_matches"]
    instance["A_matches"] = data["A_matches"]
    instance["junior_matches"] = data["junior_matches"]
    instance["matches_rest"] = data["matches_rest"]

    instance["nof_matches"] = len(data["matches"])
    instance["nof_V_matches"] = len(data["V_matches"])
    instance["nof_A_matches"] = len(data["A_matches"])
    instance["nof_junior_matches"] = len(data["junior_matches"])
    instance["nof_matches_rest"] = len(data["matches_rest"])





    # Solve
    last_solution = None
    result = instance.solutions(processes=1, optimisation_level=3, intermediate_solutions=True, verbose=True, statistics=True)

    try:
        
        async for res in result:
            if res.solution is not None:
                last_solution = res.solution
                # Access output
                schedule = build_schedule(data["class_index"], data["round_index"], res.solution.time_of_match, class_names, data)
                print("TIMESLOTS:")
                print("\n\nRESULT:")
                print(res.statistics)
                print(res.solution, end="\n\n")
                COL_WIDTH = 12
                for i, slot in enumerate(schedule):
                    print(f"Time slot {i:>2}:", end=" | ")
                    
                    for match in slot:
                        # Check if the match is empty/whitespace
                        content = match.strip()
                        if not content:
                            # Print empty space with the same column width
                            print(" " * COL_WIDTH, end=" | ")
                        else:
                            # :< means left-aligned within the fixed COL_WIDTH
                            print(f"{content:<{COL_WIDTH}}", end=" | ")
                            
                    print("") # New line
                print(f"New solution found! (Current count: {len(last_solution.time_of_match)})")    

    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n\n🛑 Interrupted by user (Ctrl+C). Finalizing best solution found...")


    #solution = result[0]
    #matches = solution.matches

    if last_solution is None:
        print("❌ No solution found.")
    else:
        #solution = result.solution[0]
        matches = last_solution.time_of_match
        print("✅ Solution found!")
        print(str(len(matches)))

        schedule = build_schedule(data["class_index"], data["round_index"], matches, class_names, data)
        print("TIMESLOTS:")
        for i, slot in enumerate(schedule):
            print(f"Time slot {i}: {slot}")

        write_schedule_to_excel(data["file_path"], schedule, colors)
        print("Printed to excel!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This swallows the exit error so you don't see a traceback
        pass




data = minizinc_data()

# 13 banor
#matches = [52, 52, 69, 69, 78, 79, 87, 87, 94, 95, 35, 35, 35, 35, 35, 35, 58, 59, 60, 60, 60, 60, 68, 68, 68, 68, 68, 68, 76, 76, 76, 76, 76, 77, 84, 85, 85, 85, 85, 85, 91, 91, 91, 97, 97, 35, 35, 50, 50, 68, 68, 78, 78, 78, 95, 95, 39, 39, 45, 46, 54, 54, 7, 7, 7, 13, 13, 13, 22, 22, 23, 29, 29, 30, 64, 64, 64, 72, 72, 47, 47, 47, 47, 47, 57, 57, 57, 57, 58, 65, 65, 65, 65, 65, 82, 82, 83, 83, 89, 89, 97, 32, 33, 46, 46, 54, 55, 69, 69, 96, 36, 36, 42, 42, 52, 52, 42, 42, 42, 42, 42, 53, 53, 53, 53, 53, 62, 62, 63, 63, 63, 69, 70, 79, 79, 89, 4, 4, 4, 13, 13, 13, 29, 29, 29, 37, 37, 67, 43, 50, 62, 6, 6, 6, 6, 12, 12, 12, 12, 18, 18, 18, 18, 28, 28, 34, 77, 77, 83, 83, 89, 90, 5, 5, 31, 32, 41, 41, 54, 55, 70, 70, 5, 5, 33, 33, 40, 40, 47, 48, 54, 54, 10, 10, 16, 16, 29, 29, 62, 62, 71, 71, 9, 9, 10, 10, 25, 25, 25, 25, 31, 31, 31, 31, 37, 37, 56, 38, 39, 39, 50, 51, 51, 57, 58, 58, 64, 64, 93, 17, 25, 32, 8, 17, 26, 73, 73, 79, 80, 87, 87, 17, 17, 29, 30, 36, 36, 42, 42, 52, 1, 1, 7, 7, 13, 13, 20, 20, 33, 33, 51, 51, 82, 82, 92, 93, 34, 34, 54, 54, 80, 80, 93, 38, 38, 47, 47, 72, 73, 97, 11, 11, 11, 11, 11, 11, 19, 19, 19, 19, 19, 19, 27, 27, 27, 27, 27, 27, 35, 64, 64, 94, 1, 3, 3, 3, 3, 17, 17, 19, 19, 19, 27, 27, 27, 27, 27, 46, 46, 70, 7, 7, 7, 7, 23, 23, 23, 23, 31, 31, 31, 31, 41, 41, 50, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 44, 44, 44, 44, 44, 44, 44, 44, 44, 44, 61, 61, 61, 61, 61, 61, 61, 61, 67, 67, 67, 67, 73, 73, 80, 5, 5, 11, 12, 30, 31, 63, 63, 71, 24, 24, 24, 24, 24, 24, 24, 24, 38, 38, 38, 38, 38, 38, 40, 40, 49, 49, 49, 49, 49, 49, 49, 49, 55, 56, 56, 56, 56, 56, 56, 56, 84, 84, 84, 85, 91, 91, 97, 21, 21, 21, 21, 21, 21, 21, 21, 59, 59, 59, 59, 59, 59, 59, 59, 66, 66, 66, 66, 66, 66, 66, 66, 74, 74, 74, 75, 75, 75, 81, 81, 81, 81, 88, 88, 94, 4, 4, 4, 14, 14, 15, 21, 21, 21, 29, 29, 44, 44, 64, 8, 8, 8, 10, 10, 33, 33, 33, 33, 34, 40, 40, 40, 40, 40, 48, 48, 48, 48, 55, 55, 70]

# 12 banor
#matches = [24, 24, 46, 46, 57, 57, 65, 65, 98, 98, 3, 3, 3, 3, 3, 3, 64, 64, 64, 64, 64, 64, 72, 72, 72, 74, 74, 74, 80, 80, 80, 80, 80, 80, 88, 88, 88, 88, 89, 89, 95, 95, 96, 102, 102, 27, 27, 67, 67, 76, 76, 94, 94, 94, 100, 100, 36, 36, 44, 44, 50, 50, 7, 7, 7, 16, 16, 16, 32, 32, 32, 40, 40, 40, 54, 54, 54, 60, 60, 11, 13, 13, 13, 13, 58, 58, 58, 58, 58, 71, 71, 71, 71, 73, 86, 86, 86, 86, 92, 92, 98, 28, 29, 42, 42, 51, 52, 58, 58, 99, 36, 37, 44, 45, 54, 54, 26, 26, 26, 26, 26, 37, 37, 37, 39, 39, 52, 52, 52, 52, 52, 60, 60, 67, 67, 100, 16, 16, 16, 47, 47, 47, 55, 55, 55, 61, 61, 67, 26, 32, 40, 9, 9, 9, 9, 15, 15, 15, 15, 21, 21, 21, 21, 47, 47, 56, 82, 82, 92, 93, 101, 101, 8, 8, 14, 14, 20, 20, 56, 57, 66, 66, 10, 10, 16, 16, 52, 52, 60, 60, 66, 66, 6, 6, 33, 33, 41, 41, 48, 48, 56, 56, 3, 3, 3, 3, 10, 11, 11, 11, 17, 17, 17, 17, 25, 25, 55, 5, 5, 5, 19, 19, 20, 48, 48, 48, 60, 60, 66, 36, 44, 55, 3, 14, 22, 67, 67, 75, 76, 82, 82, 45, 45, 57, 57, 63, 64, 82, 82, 100, 1, 1, 7, 8, 19, 19, 28, 29, 47, 47, 64, 64, 80, 80, 96, 97, 34, 34, 63, 63, 76, 76, 92, 51, 51, 59, 59, 70, 70, 102, 5, 5, 5, 5, 5, 5, 33, 33, 33, 33, 33, 33, 41, 41, 41, 41, 41, 41, 49, 62, 62, 93, 1, 1, 1, 1, 1, 9, 9, 9, 9, 9, 21, 21, 21, 21, 21, 31, 31, 69, 26, 26, 26, 26, 45, 45, 45, 45, 73, 73, 73, 73, 87, 87, 99, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 69, 69, 69, 69, 69, 69, 69, 69, 69, 69, 76, 76, 78, 78, 78, 78, 78, 78, 78, 78, 84, 84, 84, 84, 84, 84, 84, 84, 90, 90, 90, 90, 96, 96, 102, 34, 34, 42, 42, 49, 49, 69, 70, 98, 12, 12, 12, 12, 12, 12, 12, 12, 18, 18, 18, 18, 18, 18, 18, 18, 24, 24, 24, 24, 24, 24, 24, 24, 38, 38, 38, 38, 38, 38, 38, 38, 53, 53, 53, 53, 59, 59, 65, 28, 28, 28, 28, 28, 28, 28, 28, 35, 35, 35, 35, 35, 35, 35, 35, 43, 43, 43, 43, 43, 43, 43, 43, 50, 50, 50, 50, 50, 50, 62, 62, 62, 62, 82, 82, 94, 46, 46, 46, 56, 56, 56, 62, 62, 62, 85, 85, 91, 91, 97, 1, 1, 1, 1, 1, 7, 7, 7, 7, 7, 14, 14, 14, 14, 14, 22, 22, 23, 23, 39, 39, 71]

# 14 banor 

# matches = [37, 38, 59, 59, 69, 69, 81, 81, 97, 98, 34, 34, 34, 34, 34, 34, 40, 40, 40, 40, 40, 40, 55, 55, 55, 55, 56, 56, 66, 66, 68, 68, 68, 68, 83, 84, 84, 84, 84, 85, 93, 93, 94, 101, 101, 31, 31, 37, 37, 43, 43, 82, 82, 82, 98, 98, 72, 72, 78, 78, 89, 89, 2, 3, 3, 10, 10, 10, 18, 18, 18, 25, 25, 25, 51, 51, 51, 62, 62, 7, 7, 7, 7, 7, 15, 15, 15, 15, 15, 21, 21, 21, 21, 21, 28, 28, 28, 29, 36, 36, 70, 34, 35, 43, 43, 62, 62, 69, 69, 91, 43, 43, 52, 53, 59, 59, 7, 7, 7, 7, 8, 37, 37, 38, 38, 39, 64, 64, 64, 64, 64, 70, 70, 76, 76, 82, 1, 1, 1, 12, 12, 12, 18, 18, 18, 27, 27, 69, 39, 48, 55, 12, 12, 12, 12, 18, 18, 18, 18, 24, 24, 24, 24, 33, 33, 86, 80, 80, 86, 86, 99, 99, 11, 11, 19, 20, 32, 32, 40, 40, 54, 54, 8, 8, 23, 23, 31, 31, 42, 42, 82, 82, 12, 12, 18, 18, 27, 27, 70, 70, 86, 86, 13, 13, 13, 14, 41, 41, 42, 42, 64, 64, 64, 64, 76, 76, 87, 26, 26, 26, 32, 32, 32, 38, 38, 38, 54, 54, 84, 1, 12, 18, 5, 11, 17, 24, 24, 32, 32, 38, 38, 22, 23, 49, 50, 58, 59, 74, 74, 96, 69, 69, 78, 78, 88, 88, 36, 36, 57, 57, 67, 67, 92, 92, 101, 101, 51, 51, 61, 61, 69, 69, 97, 31, 31, 42, 42, 73, 73, 84, 27, 27, 27, 27, 27, 27, 45, 45, 45, 45, 45, 45, 60, 60, 60, 60, 60, 60, 70, 80, 80, 95, 4, 5, 6, 6, 6, 24, 24, 24, 24, 24, 33, 33, 33, 33, 33, 48, 48, 58, 39, 39, 39, 39, 54, 54, 54, 54, 64, 64, 64, 64, 76, 76, 89, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 48, 48, 48, 48, 48, 48, 48, 48, 48, 48, 57, 57, 57, 57, 57, 57, 57, 57, 57, 57, 67, 67, 67, 67, 67, 67, 67, 67, 73, 73, 73, 73, 92, 92, 98, 53, 53, 62, 63, 77, 77, 90, 90, 96, 9, 9, 9, 9, 9, 9, 9, 9, 15, 15, 15, 15, 15, 15, 15, 15, 21, 21, 21, 21, 21, 21, 21, 21, 30, 30, 30, 30, 30, 30, 30, 30, 36, 36, 36, 36, 42, 42, 83, 1, 1, 1, 1, 1, 1, 1, 1, 45, 45, 45, 45, 45, 45, 45, 45, 51, 51, 51, 51, 51, 51, 51, 51, 61, 61, 61, 61, 61, 61, 79, 79, 79, 79, 95, 95, 101, 53, 53, 53, 59, 59, 59, 65, 66, 66, 75, 75, 94, 95, 101, 7, 7, 9, 9, 9, 29, 29, 29, 29, 29, 35, 35, 35, 35, 35, 41, 41, 41, 41, 70, 70, 89]

#time_of_match=[11, 21, 21, 21, 21, 27, 27, 33, 33, 37, 43, 49, 37, 43, 49, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 21, 21, 21, 21, 21, 21, 21, 21, 33, 33, 33, 33, 41, 41, 49, 49, 21, 21, 34, 34, 34, 34, 40, 40, 46, 46, 9, 17, 17, 25, 25, 13, 29, 29, 29, 29, 37, 37, 45, 45, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 31, 31, 31, 31, 31, 31, 31, 31, 37, 37, 37, 37, 43, 43, 49, 15, 15, 15, 21, 21, 21, 21, 27, 27, 33, 7, 7, 13, 13, 13, 13, 19, 19, 27, 37, 37, 43, 43, 49, 5, 5, 5, 5, 5, 5, 11, 11, 11, 11, 11, 11, 11, 11, 17, 17, 17, 17, 25, 25, 31, 19, 25, 31, 35, 41, 47, 37, 43, 43, 49]
'''
time_of_match=[1, 7, 7, 7, 7, 13, 13, 21, 21, 1, 7, 13, 25, 31, 37, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 9, 9, 9, 9, 9, 9, 9, 9, 29, 29, 29, 29, 37, 37, 45, 45, 1, 1, 9, 9, 9, 9, 17, 17, 25, 25, 5, 13, 13, 21, 21, 17, 25, 25, 25, 25, 33, 33, 41, 41, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 7, 7, 7, 7, 7, 7, 7, 7, 13, 13, 13, 13, 21, 21, 29, 1, 1, 1, 7, 7, 7, 7, 13, 13, 21, 17, 17, 25, 25, 25, 25, 33, 33, 39, 28, 28, 34, 34, 40, 1, 1, 1, 1, 1, 1, 7, 7, 7, 7, 7, 7, 7, 7, 13, 13, 13, 13, 21, 21, 27, 1, 7, 13, 31, 37, 43, 31, 37, 37, 43]

schedule = build_schedule(data["class_index"], data["round_index"], time_of_match, class_names, data)
print("TIMESLOTS:")

for i, slot in enumerate(schedule):
    if i < 10:
        print(f"Time slot {i}:  ", end=" | ")
    else:
        print(f"Time slot {i}: ", end=" | ")
    for match in slot:
        print(match, end=" | ")
    print("")

print(f"Total matches from minizinc: {str(len(time_of_match))}")
total_matches = sum(1 for slot in schedule for match in slot if match.strip())
print(f"Total matches in schedule: {total_matches}")

write_schedule_to_excel(data["file_path"], schedule, colors)


'''
