import minizinc
import asyncio
from parse_excel import minizinc_data


from openpyxl import load_workbook, Workbook
from openpyxl.styles import PatternFill

from datetime import datetime, timedelta

from openpyxl.styles import PatternFill, Font
from openpyxl.utils import get_column_letter

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
            match_name = f"{class_names[class_id - 1]} - {round_id}"
            schedule[time_slot-1][count] = match_name
            slot_counts[time_slot-1] += 1
        else:
            # Optional: warn if slot overflows
            print(f"‼️ WARNING: time slot {time_slot-1} already full! match {match_name} not added to schedule")

    return schedule


def write_schedule_to_excel(file_path, schedule, event_colors, start_time_str, num_courts=12, sheet_name="timetable", start_row=2, start_col=2):
    try:
        book = load_workbook(file_path)
    except FileNotFoundError:
        print(f"❌ Error: The file '{file_path}' was not found. Skipping writing the schedule to Excel.")
        return

    if sheet_name in book.sheetnames:
        del book[sheet_name]
    
    sheet = book.create_sheet(sheet_name)

    fmt = "%H:%M"
    current_time = datetime.strptime(start_time_str, fmt)
    end_limit = datetime.strptime("21:00", fmt)
    
    current_section_start_row = start_row
    relative_col_offset = 0
    
    match_found_count = 0
    match_fail_count = 0

    # We need to know the total columns in a section to define the COUNTA range
    # Let's calculate how many slots fit between start_time and 21:00
    # Or more simply, we can determine the end column of the current section block
    
    for slot_idx, time_slot in enumerate(schedule):
        if current_time > end_limit:
            # 12 rows (courts) + 1 row (formula) + 5 rows gap (3 original + 2 new)
            current_section_start_row += (num_courts + 6)
            current_time = datetime.strptime("09:00", fmt)
            relative_col_offset = 0
            
        actual_col = start_col + relative_col_offset
        col_letter = get_column_letter(actual_col)
        
        # 1. Write Time Header
        sheet.cell(row=current_section_start_row - 1, column=actual_col).value = current_time.strftime(fmt)
        
        # 2. Write Row Numbers (Courts)
        for i in range(num_courts):
            sheet.cell(row=current_section_start_row + i, column=start_col - 1).value = i + 1

        # 3. Write Matches
        for row_idx_offset, match in enumerate(time_slot):
            if row_idx_offset >= num_courts:
                break
                
            full_match_text = str(match).strip() if match else ""
            if not full_match_text:
                continue

            actual_row = current_section_start_row + row_idx_offset
            cell = sheet.cell(row=actual_row, column=actual_col)
            cell.value = full_match_text

            lookup_key = full_match_text.split(" -")[0].strip()
            if lookup_key in event_colors:
                hex_bg, text_choice = event_colors[lookup_key]
                clean_hex = hex_bg.replace("#", "")
                cell.fill = PatternFill(start_color=clean_hex, end_color=clean_hex, fill_type="solid")
                font_hex = "000000" if text_choice == "black" else "FFFFFF"
                cell.font = Font(color=font_hex)
                match_found_count += 1
            else:
                match_fail_count += 1

        # 4. Add COUNTA Formula
        # Formula range: From current row to (current row + num_courts - 1)
        # And from current column to the end of the schedule (or end of section)
        first_row = current_section_start_row
        last_row = current_section_start_row + num_courts - 1
        
        last_col_letter = get_column_letter(actual_col + 1)
        
        formula_row = last_row + 1
        formula_cell = sheet.cell(row=formula_row, column=actual_col)
        # Example: =COUNTA(C4:D15)
        formula_cell.value = f"=COUNTA({col_letter}{first_row}:{last_col_letter}{last_row})"

        current_time += timedelta(minutes=15)
        relative_col_offset += 1

    book.save(file_path)
    print(f"➡️  Schedule written with {num_courts} courts and extra spacing.")



def print_in_terminal(schedule, start_time_str):
    COL_WIDTH = 12

    # 1. Convert start_time to total minutes
    h, m = map(int, start_time_str.split(':'))
    start_minutes = h * 60 + m

    # Define the cycle length
    CYCLE_MINUTES = 735 

    for i, slot in enumerate(schedule):
        # 2. Calculate minutes elapsed from the start
        elapsed = i * 15
        
        # 3. Use modulo to wrap around the 12-hour window
        # This keeps the time within [start_minutes, start_minutes + 720]
        current_minutes = start_minutes + (elapsed % CYCLE_MINUTES)
        
        # 4. Handle 24-hour clock overflow (e.g., if 21:00 + 15 mins goes to 21:15)
        # This ensures we don't get "25:15" if your start time is late in the day
        display_total_minutes = current_minutes % 1440
        
        display_h = display_total_minutes // 60
        display_m = display_total_minutes % 60
        time_label = f"{display_h:02d}:{display_m:02d}"

        print(f"{time_label}:", end=" | ")
        
        for match in slot:
            content = match.strip()
            if not content:
                print(" " * COL_WIDTH, end=" | ")
            else:
                print(f"{content:<{COL_WIDTH}}", end=" | ")
                
        print("")




async def main():
    print("\n\n----Running Constraintsolver.py----\n")
    # Load model
    model = minizinc.Model("model_elite.mzn")

    data = minizinc_data(False)
    if not data:
        print("❌ ERROR: No data was loaded. QUITTING!")
        print("\n----Done due to error----\n")
        return

    print(data)
    
    # Choose solver (you can replace "gecode" with another installed solver)
    solver = minizinc.Solver.lookup("cp-sat")
    #solver = minizinc.Solver.lookup("gecode")

    # Create instance and give input
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
    result = instance.solutions(processes=4, optimisation_level=3, intermediate_solutions=True, verbose=True, statistics=True)

    try:
        
        async for res in result:
            if res.solution is not None:
                last_solution = res.solution
                # Access output
                schedule = build_schedule(data["class_index"], data["round_index"], res.solution.time_of_match, list(data["event_colors"].keys()), data)
                print("TIMESLOTS:")
                print("\n\nRESULT:")
                print(res.statistics)
                print(res.solution, end="\n\n")
                print_in_terminal(schedule, "09:00")
                print(f"New solution found! (Current count: {len(last_solution.time_of_match)})")    

    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n\n🛑 Interrupted by user (Ctrl+C). Finalizing best solution found...")


    #solution = result[0]
    #matches = solution.matches

    if last_solution is None:
        print("❌ No solution found.")
        print(res.status)
    else:
        #solution = result.solution[0]
        matches = last_solution.time_of_match
        print("✅ Solution found!")
        print(str(len(matches)))

        schedule = build_schedule(data["class_index"], data["round_index"], matches, list(data["event_colors"].keys()), data)
        print_in_terminal(schedule, "09:00")

        write_schedule_to_excel(data["file_path"], schedule, data["event_colors"], "09:00", sheet_name="timetable", start_row=4, start_col=3)
        print("Printed to excel!")

    print("\n----Done----\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This swallows the exit error so you don't see a traceback
        pass


'''
print("\n\n----Running pre-saved mach times----\n")

data = minizinc_data(False)

# 13 banor
#matches = [52, 52, 69, 69, 78, 79, 87, 87, 94, 95, 35, 35, 35, 35, 35, 35, 58, 59, 60, 60, 60, 60, 68, 68, 68, 68, 68, 68, 76, 76, 76, 76, 76, 77, 84, 85, 85, 85, 85, 85, 91, 91, 91, 97, 97, 35, 35, 50, 50, 68, 68, 78, 78, 78, 95, 95, 39, 39, 45, 46, 54, 54, 7, 7, 7, 13, 13, 13, 22, 22, 23, 29, 29, 30, 64, 64, 64, 72, 72, 47, 47, 47, 47, 47, 57, 57, 57, 57, 58, 65, 65, 65, 65, 65, 82, 82, 83, 83, 89, 89, 97, 32, 33, 46, 46, 54, 55, 69, 69, 96, 36, 36, 42, 42, 52, 52, 42, 42, 42, 42, 42, 53, 53, 53, 53, 53, 62, 62, 63, 63, 63, 69, 70, 79, 79, 89, 4, 4, 4, 13, 13, 13, 29, 29, 29, 37, 37, 67, 43, 50, 62, 6, 6, 6, 6, 12, 12, 12, 12, 18, 18, 18, 18, 28, 28, 34, 77, 77, 83, 83, 89, 90, 5, 5, 31, 32, 41, 41, 54, 55, 70, 70, 5, 5, 33, 33, 40, 40, 47, 48, 54, 54, 10, 10, 16, 16, 29, 29, 62, 62, 71, 71, 9, 9, 10, 10, 25, 25, 25, 25, 31, 31, 31, 31, 37, 37, 56, 38, 39, 39, 50, 51, 51, 57, 58, 58, 64, 64, 93, 17, 25, 32, 8, 17, 26, 73, 73, 79, 80, 87, 87, 17, 17, 29, 30, 36, 36, 42, 42, 52, 1, 1, 7, 7, 13, 13, 20, 20, 33, 33, 51, 51, 82, 82, 92, 93, 34, 34, 54, 54, 80, 80, 93, 38, 38, 47, 47, 72, 73, 97, 11, 11, 11, 11, 11, 11, 19, 19, 19, 19, 19, 19, 27, 27, 27, 27, 27, 27, 35, 64, 64, 94, 1, 3, 3, 3, 3, 17, 17, 19, 19, 19, 27, 27, 27, 27, 27, 46, 46, 70, 7, 7, 7, 7, 23, 23, 23, 23, 31, 31, 31, 31, 41, 41, 50, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 44, 44, 44, 44, 44, 44, 44, 44, 44, 44, 61, 61, 61, 61, 61, 61, 61, 61, 67, 67, 67, 67, 73, 73, 80, 5, 5, 11, 12, 30, 31, 63, 63, 71, 24, 24, 24, 24, 24, 24, 24, 24, 38, 38, 38, 38, 38, 38, 40, 40, 49, 49, 49, 49, 49, 49, 49, 49, 55, 56, 56, 56, 56, 56, 56, 56, 84, 84, 84, 85, 91, 91, 97, 21, 21, 21, 21, 21, 21, 21, 21, 59, 59, 59, 59, 59, 59, 59, 59, 66, 66, 66, 66, 66, 66, 66, 66, 74, 74, 74, 75, 75, 75, 81, 81, 81, 81, 88, 88, 94, 4, 4, 4, 14, 14, 15, 21, 21, 21, 29, 29, 44, 44, 64, 8, 8, 8, 10, 10, 33, 33, 33, 33, 34, 40, 40, 40, 40, 40, 48, 48, 48, 48, 55, 55, 70]

# 12 banor
#time_of_match = [24, 24, 46, 46, 57, 57, 65, 65, 98, 98, 3, 3, 3, 3, 3, 3, 64, 64, 64, 64, 64, 64, 72, 72, 72, 74, 74, 74, 80, 80, 80, 80, 80, 80, 88, 88, 88, 88, 89, 89, 95, 95, 96, 102, 102, 27, 27, 67, 67, 76, 76, 94, 94, 94, 100, 100, 36, 36, 44, 44, 50, 50, 7, 7, 7, 16, 16, 16, 32, 32, 32, 40, 40, 40, 54, 54, 54, 60, 60, 11, 13, 13, 13, 13, 58, 58, 58, 58, 58, 71, 71, 71, 71, 73, 86, 86, 86, 86, 92, 92, 98, 28, 29, 42, 42, 51, 52, 58, 58, 99, 36, 37, 44, 45, 54, 54, 26, 26, 26, 26, 26, 37, 37, 37, 39, 39, 52, 52, 52, 52, 52, 60, 60, 67, 67, 100, 16, 16, 16, 47, 47, 47, 55, 55, 55, 61, 61, 67, 26, 32, 40, 9, 9, 9, 9, 15, 15, 15, 15, 21, 21, 21, 21, 47, 47, 56, 82, 82, 92, 93, 101, 101, 8, 8, 14, 14, 20, 20, 56, 57, 66, 66, 10, 10, 16, 16, 52, 52, 60, 60, 66, 66, 6, 6, 33, 33, 41, 41, 48, 48, 56, 56, 3, 3, 3, 3, 10, 11, 11, 11, 17, 17, 17, 17, 25, 25, 55, 5, 5, 5, 19, 19, 20, 48, 48, 48, 60, 60, 66, 36, 44, 55, 3, 14, 22, 67, 67, 75, 76, 82, 82, 45, 45, 57, 57, 63, 64, 82, 82, 100, 1, 1, 7, 8, 19, 19, 28, 29, 47, 47, 64, 64, 80, 80, 96, 97, 34, 34, 63, 63, 76, 76, 92, 51, 51, 59, 59, 70, 70, 102, 5, 5, 5, 5, 5, 5, 33, 33, 33, 33, 33, 33, 41, 41, 41, 41, 41, 41, 49, 62, 62, 93, 1, 1, 1, 1, 1, 9, 9, 9, 9, 9, 21, 21, 21, 21, 21, 31, 31, 69, 26, 26, 26, 26, 45, 45, 45, 45, 73, 73, 73, 73, 87, 87, 99, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 69, 69, 69, 69, 69, 69, 69, 69, 69, 69, 76, 76, 78, 78, 78, 78, 78, 78, 78, 78, 84, 84, 84, 84, 84, 84, 84, 84, 90, 90, 90, 90, 96, 96, 102, 34, 34, 42, 42, 49, 49, 69, 70, 98, 12, 12, 12, 12, 12, 12, 12, 12, 18, 18, 18, 18, 18, 18, 18, 18, 24, 24, 24, 24, 24, 24, 24, 24, 38, 38, 38, 38, 38, 38, 38, 38, 53, 53, 53, 53, 59, 59, 65, 28, 28, 28, 28, 28, 28, 28, 28, 35, 35, 35, 35, 35, 35, 35, 35, 43, 43, 43, 43, 43, 43, 43, 43, 50, 50, 50, 50, 50, 50, 62, 62, 62, 62, 82, 82, 94, 46, 46, 46, 56, 56, 56, 62, 62, 62, 85, 85, 91, 91, 97, 1, 1, 1, 1, 1, 7, 7, 7, 7, 7, 14, 14, 14, 14, 14, 22, 22, 23, 23, 39, 39, 71]

# 14 banor 

# matches = [37, 38, 59, 59, 69, 69, 81, 81, 97, 98, 34, 34, 34, 34, 34, 34, 40, 40, 40, 40, 40, 40, 55, 55, 55, 55, 56, 56, 66, 66, 68, 68, 68, 68, 83, 84, 84, 84, 84, 85, 93, 93, 94, 101, 101, 31, 31, 37, 37, 43, 43, 82, 82, 82, 98, 98, 72, 72, 78, 78, 89, 89, 2, 3, 3, 10, 10, 10, 18, 18, 18, 25, 25, 25, 51, 51, 51, 62, 62, 7, 7, 7, 7, 7, 15, 15, 15, 15, 15, 21, 21, 21, 21, 21, 28, 28, 28, 29, 36, 36, 70, 34, 35, 43, 43, 62, 62, 69, 69, 91, 43, 43, 52, 53, 59, 59, 7, 7, 7, 7, 8, 37, 37, 38, 38, 39, 64, 64, 64, 64, 64, 70, 70, 76, 76, 82, 1, 1, 1, 12, 12, 12, 18, 18, 18, 27, 27, 69, 39, 48, 55, 12, 12, 12, 12, 18, 18, 18, 18, 24, 24, 24, 24, 33, 33, 86, 80, 80, 86, 86, 99, 99, 11, 11, 19, 20, 32, 32, 40, 40, 54, 54, 8, 8, 23, 23, 31, 31, 42, 42, 82, 82, 12, 12, 18, 18, 27, 27, 70, 70, 86, 86, 13, 13, 13, 14, 41, 41, 42, 42, 64, 64, 64, 64, 76, 76, 87, 26, 26, 26, 32, 32, 32, 38, 38, 38, 54, 54, 84, 1, 12, 18, 5, 11, 17, 24, 24, 32, 32, 38, 38, 22, 23, 49, 50, 58, 59, 74, 74, 96, 69, 69, 78, 78, 88, 88, 36, 36, 57, 57, 67, 67, 92, 92, 101, 101, 51, 51, 61, 61, 69, 69, 97, 31, 31, 42, 42, 73, 73, 84, 27, 27, 27, 27, 27, 27, 45, 45, 45, 45, 45, 45, 60, 60, 60, 60, 60, 60, 70, 80, 80, 95, 4, 5, 6, 6, 6, 24, 24, 24, 24, 24, 33, 33, 33, 33, 33, 48, 48, 58, 39, 39, 39, 39, 54, 54, 54, 54, 64, 64, 64, 64, 76, 76, 89, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 48, 48, 48, 48, 48, 48, 48, 48, 48, 48, 57, 57, 57, 57, 57, 57, 57, 57, 57, 57, 67, 67, 67, 67, 67, 67, 67, 67, 73, 73, 73, 73, 92, 92, 98, 53, 53, 62, 63, 77, 77, 90, 90, 96, 9, 9, 9, 9, 9, 9, 9, 9, 15, 15, 15, 15, 15, 15, 15, 15, 21, 21, 21, 21, 21, 21, 21, 21, 30, 30, 30, 30, 30, 30, 30, 30, 36, 36, 36, 36, 42, 42, 83, 1, 1, 1, 1, 1, 1, 1, 1, 45, 45, 45, 45, 45, 45, 45, 45, 51, 51, 51, 51, 51, 51, 51, 51, 61, 61, 61, 61, 61, 61, 79, 79, 79, 79, 95, 95, 101, 53, 53, 53, 59, 59, 59, 65, 66, 66, 75, 75, 94, 95, 101, 7, 7, 9, 9, 9, 29, 29, 29, 29, 29, 35, 35, 35, 35, 35, 41, 41, 41, 41, 70, 70, 89]

#time_of_match=[11, 21, 21, 21, 21, 27, 27, 33, 33, 37, 43, 49, 37, 43, 49, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 21, 21, 21, 21, 21, 21, 21, 21, 33, 33, 33, 33, 41, 41, 49, 49, 21, 21, 34, 34, 34, 34, 40, 40, 46, 46, 9, 17, 17, 25, 25, 13, 29, 29, 29, 29, 37, 37, 45, 45, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 23, 31, 31, 31, 31, 31, 31, 31, 31, 37, 37, 37, 37, 43, 43, 49, 15, 15, 15, 21, 21, 21, 21, 27, 27, 33, 7, 7, 13, 13, 13, 13, 19, 19, 27, 37, 37, 43, 43, 49, 5, 5, 5, 5, 5, 5, 11, 11, 11, 11, 11, 11, 11, 11, 17, 17, 17, 17, 25, 25, 31, 19, 25, 31, 35, 41, 47, 37, 43, 43, 49]
time_of_match=[19, 19, 29, 29, 36, 36, 43, 43, 93, 93, 5, 5, 5, 5, 5, 5, 33, 33, 33, 33, 33, 33, 45, 45, 45, 45, 45, 45, 55, 55, 55, 55, 55, 55, 65, 65, 65, 65, 65, 65, 71, 71, 71, 95, 95, 1, 1, 34, 34, 45, 45, 66, 66, 66, 72, 72, 13, 13, 21, 21, 27, 27, 39, 39, 39, 50, 50, 50, 60, 60, 60, 77, 77, 77, 83, 83, 83, 89, 89, 11, 11, 11, 11, 11, 37, 37, 37, 37, 37, 51, 51, 51, 51, 51, 61, 61, 61, 61, 91, 91, 97, 9, 9, 15, 15, 21, 21, 27, 27, 77, 67, 67, 73, 73, 79, 79, 7, 7, 7, 7, 7, 19, 19, 19, 19, 19, 25, 25, 25, 25, 25, 33, 33, 73, 73, 79, 43, 43, 43, 54, 54, 54, 61, 61, 61, 81, 81, 94, 23, 29, 35, 43, 43, 43, 43, 53, 53, 53, 53, 67, 67, 67, 67, 88, 88, 94, 3, 3, 16, 16, 22, 22, 24, 24, 30, 30, 41, 41, 90, 90, 96, 96, 33, 33, 44, 44, 52, 52, 59, 59, 97, 97, 7, 7, 14, 14, 20, 20, 69, 69, 79, 79, 23, 23, 23, 23, 41, 41, 41, 41, 58, 58, 58, 58, 67, 67, 84, 29, 29, 29, 35, 35, 35, 77, 77, 77, 86, 86, 92, 43, 52, 60, 32, 38, 49, 63, 63, 69, 69, 79, 79, 3, 3, 47, 47, 55, 55, 62, 62, 71, 81, 81, 87, 87, 93, 93, 11, 11, 40, 40, 65, 65, 73, 73, 81, 81, 18, 18, 26, 26, 69, 69, 77, 47, 47, 59, 59, 87, 87, 95, 5, 5, 5, 5, 5, 5, 13, 13, 13, 13, 13, 13, 21, 21, 21, 21, 21, 21, 35, 46, 46, 66, 11, 11, 11, 11, 11, 23, 23, 23, 23, 23, 35, 35, 35, 35, 35, 51, 51, 63, 29, 29, 29, 29, 41, 41, 41, 41, 56, 56, 56, 56, 83, 83, 92, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 49, 49, 49, 49, 49, 49, 49, 49, 63, 63, 63, 63, 70, 70, 80, 7, 7, 13, 13, 45, 45, 51, 51, 63, 27, 27, 27, 27, 27, 27, 28, 28, 38, 39, 39, 39, 39, 39, 39, 39, 57, 57, 57, 57, 57, 57, 57, 57, 75, 75, 75, 75, 75, 75, 75, 75, 85, 85, 85, 85, 91, 91, 97, 3, 3, 3, 3, 3, 3, 3, 3, 15, 15, 15, 15, 15, 15, 15, 15, 31, 31, 31, 31, 31, 31, 31, 32, 47, 47, 47, 47, 47, 47, 64, 64, 64, 64, 71, 71, 81, 7, 7, 7, 19, 19, 19, 31, 31, 31, 42, 42, 48, 48, 82, 25, 25, 25, 25, 25, 37, 37, 37, 37, 37, 53, 53, 53, 53, 53, 59, 59, 59, 59, 89, 89, 95]

schedule = build_schedule(data["class_index"], data["round_index"], time_of_match, list(data["event_colors"].keys()), data)
print("TIMESLOTS:")

print_in_terminal(schedule, "09:00")

print(f"Total matches from minizinc: {str(len(time_of_match))}")
total_matches = sum(1 for slot in schedule for match in slot if match.strip())
print(f"Total matches in schedule: {total_matches}")

write_schedule_to_excel(data["file_path"], schedule, data["event_colors"], "18:00", sheet_name="timetable", start_row=4, start_col=3)
#write_schedule_to_excel(data["file_path"], schedule, sheet_name="timetable", start_row=4, start_col=4)

print("\n----Done----\n")
'''