import minizinc
import asyncio
from parse_excel import minizinc_data


from openpyxl import load_workbook, Workbook
from openpyxl.styles import PatternFill



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
    Writes the schedule to an Excel sheet.
    Each time slot is written as a column.
    Overwrites the sheet if it already exists.
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
    else:
        sheet = book.create_sheet(sheet_name)

    # Mapping class prefix -> color
    class_color_map = {
        key: PatternFill(start_color=value, end_color=value, fill_type="solid")
        for key, value in colors.items()
    }

    # Write the schedule
    # Transpose so each time slot is a column
    for col_idx, time_slot in enumerate(schedule, start=start_col):
        for row_idx, match in enumerate(time_slot, start=start_row):
            if match == "        ":
                continue

            # Write match
            cell = sheet.cell(row=row_idx, column=col_idx)
            cell.value = match

            # Determine class prefix
            match_clean = str(match).strip()
            words = match_clean.split()
            class_prefix = " ".join(words[:2])
            #class_prefix = match[:4]

            # Assign color if not yet assigned
            #if class_prefix not in class_color_map:
            #   color_idx = len(class_color_map) % len(colors)
            #  class_color_map[class_prefix] = PatternFill(start_color=colors[color_idx],
            #                                             end_color=colors[color_idx],
                #                                            fill_type="solid")
            # Apply fill
            cell.fill = class_color_map[class_prefix]
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
'''
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

class_names = [
    "BS U11", "BS U13", "GS U13", "XD U13", "BD U13", 
    "BS U15", "GS U15", "BD U15",
    "BS U17", "GS U17", "XD U17", "BD U17", "GD U17", 
    "MD 40", "MD 45", "XD 45", "MD 50", "MD 55", "XD 55",
    "MD 60", "XD 60", "MD 65", "MD 70",
    "MD V", "WD V", "XD V", "MD A", "WD A", "XD A",
    "MD B", "WD B", "XD B", "MD C", "WD C", "XD C"
]




async def main():
    # Load model
    model = minizinc.Model("model_tof.mzn")

    data = minizinc_data()



    # Choose solver (you can replace "gecode" with another installed solver)
    solver = minizinc.Solver.lookup("cp-sat")
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
    #result = instance.solve(nr_solutions=1, processes=1, optimisation_level=1)
    result = instance.solutions(processes=4, optimisation_level=3, intermediate_solutions=True, verbose=True, statistics=True)

    last_solution = None
    async for res in result:

        # Access output
        print("\n\nRESULT:")
        print(res.statistics)
        print(res.solution, end="\n\n")

        if res.solution is None:
            continue
        else:
            schedule = build_schedule(data["class_index"], data["round_index"], res.solution.time_of_match, class_names, data)
            print("TIMESLOTS:")
            '''
            for i, slot in enumerate(schedule):
                if i < 10:
                    print(f"Time slot {i}:  ", end=" | ")
                else:
                    print(f"Time slot {i}: ", end=" | ")
                for match in slot:
                    print(match, end=" | ")
                print("")
            '''
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

            last_solution = res.solution



    #solution = result[0]
    #matches = solution.matches

    if last_solution is None:
        print("❌ No solution found.")
    else:
        #solution = result.solution[0]
        matches = last_solution.time_of_match
        print("✅ Solution found!")

        schedule = build_schedule(data["class_index"], data["round_index"], matches, class_names, data)
        print("TIMESLOTS:")
        for i, slot in enumerate(schedule):
            print(f"Time slot {i}: {slot}")

        write_schedule_to_excel(data["file_path"], schedule, colors)


asyncio.run(main())





data = minizinc_data()

matches = [32, 33, 71, 71, 79, 79, 95, 95, 104, 104, 36, 36, 36, 36, 36, 36, 44, 44, 44, 44, 44, 45, 53, 53, 53, 53, 53, 53, 69, 69, 69, 71, 71, 71, 88, 88, 90, 90, 90, 90, 98, 98, 98, 106, 106, 70, 70, 79, 79, 87, 87, 98, 98, 98, 106, 106, 16, 16, 24, 24, 32, 32, 28, 28, 28, 40, 40, 40, 49, 49, 49, 57, 57, 57, 65, 65, 65, 83, 83, 25, 25, 25, 25, 25, 68, 68, 68, 68, 68, 76, 76, 76, 76, 76, 84, 85, 85, 85, 95, 95, 104, 64, 64, 72, 72, 84, 85, 94, 94, 104, 80, 80, 91, 91, 99, 99, 21, 21, 22, 23, 23, 32, 33, 33, 33, 33, 52, 52, 52, 52, 52, 83, 84, 96, 97, 106, 26, 26, 26, 61, 61, 61, 69, 69, 70, 92, 92, 100, 87, 96, 106, 38, 38, 38, 38, 47, 47, 47, 47, 56, 56, 56, 56, 64, 64, 101, 40, 41, 49, 49, 57, 57, 37, 37, 75, 75, 88, 88, 96, 96, 106, 106, 45, 45, 80, 80, 88, 88, 96, 96, 104, 104, 26, 27, 40, 41, 49, 49, 63, 63, 100, 100, 37, 37, 37, 38, 55, 56, 56, 56, 64, 64, 64, 64, 72, 72, 103, 33, 34, 34, 45, 45, 46, 55, 55, 55, 75, 76, 104, 84, 92, 100, 14, 22, 30, 83, 83, 93, 93, 101, 102, 38, 38, 50, 50, 65, 66, 91, 92, 100, 86, 87, 96, 97, 105, 105, 34, 34, 47, 48, 58, 58, 71, 71, 99, 99, 29, 30, 40, 40, 63, 63, 71, 67, 67, 77, 78, 94, 94, 103, 46, 46, 46, 46, 46, 46, 54, 54, 54, 54, 54, 54, 62, 62, 62, 62, 62, 62, 70, 78, 78, 102, 58, 58, 60, 60, 60, 78, 78, 78, 78, 78, 86, 86, 86, 86, 86, 94, 94, 102, 74, 74, 74, 74, 82, 82, 82, 82, 90, 90, 90, 90, 98, 98, 106, 28, 29, 29, 29, 29, 29, 29, 29, 30, 30, 41, 41, 42, 42, 42, 42, 42, 42, 42, 42, 50, 50, 50, 51, 51, 51, 51, 51, 51, 51, 59, 59, 59, 59, 59, 59, 59, 59, 67, 67, 67, 67, 85, 85, 93, 27, 27, 66, 66, 77, 77, 93, 93, 101, 20, 20, 20, 20, 20, 20, 20, 20, 34, 34, 35, 35, 35, 35, 35, 35, 73, 73, 73, 73, 73, 73, 73, 73, 81, 81, 81, 81, 81, 81, 81, 81, 89, 89, 89, 89, 97, 97, 105, 14, 14, 14, 14, 14, 14, 14, 14, 23, 23, 23, 23, 23, 23, 23, 23, 31, 31, 31, 31, 31, 31, 31, 31, 43, 43, 43, 43, 44, 44, 60, 61, 61, 61, 69, 69, 92, 14, 14, 14, 66, 66, 67, 76, 76, 76, 84, 84, 92, 92, 102, 18, 19, 19, 19, 19, 27, 27, 27, 27, 27, 39, 39, 39, 39, 39, 48, 48, 48, 48, 88, 88, 96]

schedule = build_schedule(data["class_index"], data["round_index"], matches, class_names, data)
print("TIMESLOTS:")
for i, slot in enumerate(schedule):
    if i < 10:
        print(f"Time slot {i}:  ", end=" | ")
    else:
        print(f"Time slot {i}: ", end=" | ")
    for match in slot:
        print(match, end=" | ")
    print("")

write_schedule_to_excel(data["file_path"], schedule, colors)


