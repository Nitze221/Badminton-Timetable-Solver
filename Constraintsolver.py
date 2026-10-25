import minizinc
import asyncio
from parse_excel import minizinc_data
from parse_excel import get_blocks_for_schedule_printing


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
    #num_groups = data["timeslots_12_fields"] + data["timeslots_8_fields"] + data["timeslots_6_fields"]  # assuming time slots start at 0
    num_groups = sum(data["block_timeslots"])
    # Determine the maximum number of fields needed for the schedule grid
    max_fields = max(data["block_fields"])
    
    # Build a list to know how many fields are in each individual time slot
    fields_per_slot = [0] * num_groups
    for b in range(data["nof_blocks"]):
        start = data["block_starts"][b] - 1
        for i in range(start, start + data["block_timeslots"][b]):
            fields_per_slot[i] = data["block_fields"][b]


    # Initialize 2D list of None values (each slot has 10 possible matches)
    #schedule = [["        " for _ in range(data["fields_1"])] for _ in range(num_groups)]
    schedule = [["        " for _ in range(max_fields)] for _ in range(num_groups)]

    # Track how many matches are already in each time slot
    slot_counts = [0] * num_groups

    # Go through each match
    for match_index, time_slot in enumerate(time_of_match):
        # Find current count for this slot
        # group_slot = (time_slot - 1) // data["fields"]  # group every 10 slots together
        count = slot_counts[time_slot-1]
        
        match_index_plus_one = match_index + 1     # since matches index starts with 1
        # Only place if there’s still space
        #if count < data["fields_1"]:
        if count < fields_per_slot[time_slot-1]:
            class_id = find_class(match_index_plus_one, class_index)
            round_id = find_round(match_index_plus_one, class_index, round_index)
            match_name = f"{class_names[class_id - 1]} - {round_id}"
            schedule[time_slot-1][count] = match_name
            slot_counts[time_slot-1] += 1
        else:
            # Optional: warn if slot overflows
            print(f"‼️ WARNING: time slot {time_slot-1} already full! match {match_name} not added to schedule")

    return schedule

'''
def write_schedule_to_excel(file_path, schedule, event_colors, days_blocks, sheet_name, start_row, start_col):
    try:
        book = load_workbook(file_path)
    except FileNotFoundError:
        print(f"❌ Error: The file '{file_path}' was not found. Skipping writing the schedule to Excel.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    sheet_name = f"{sheet_name} {timestamp}"

    if sheet_name in book.sheetnames:
        del book[sheet_name]
    
    sheet = book.create_sheet(sheet_name)

    fmt = "%H:%M"
    
    current_section_start_row = start_row
    relative_col_offset = 0
    
    match_found_count = 0
    match_fail_count = 0

    # Initialize from the first block
    day_idx = 0
    block_idx = 0
    slots_processed_in_block = 0

    current_time = datetime.strptime(days_blocks[day_idx][block_idx][2], fmt)
    num_courts = days_blocks[day_idx][block_idx][1]
    max_courts_current_day = max(b[1] for b in days_blocks[day_idx])

    # We need to know the total columns in a section to define the COUNTA range
    # Let's calculate how many slots fit between start_time and 21:00
    # Or more simply, we can determine the end column of the current section block
    
    #   Print court numbers for the very first day
    for i in range(max_courts_current_day):
        sheet.cell(row=current_section_start_row + i, column=start_col - 1).value = i + 1

    for slot_idx, time_slot in enumerate(schedule):
        # Check if we have filled all the 15-minute timeslots for the current block
        if slots_processed_in_block >= days_blocks[day_idx][block_idx][0]:
            block_idx += 1
            slots_processed_in_block = 0
            
            # Check if we have finished all blocks for the current day
            if block_idx >= len(days_blocks[day_idx]):
                # Shift rows down for the new day based on the max courts used
                current_section_start_row += (max_courts_current_day + 6)
                
                day_idx += 1
                if day_idx >= len(days_blocks):
                    break # Safety catch if the schedule is longer than defined days
                
                block_idx = 0
                relative_col_offset = 0
                
                # Setup the new day
                max_courts_current_day = max(b[1] for b in days_blocks[day_idx])
                
                # Print court numbers for the new day
                for i in range(max_courts_current_day):
                    sheet.cell(row=current_section_start_row + i, column=start_col - 1).value = i + 1
                    
            # Update time and courts for the next block (whether same day or new day)
            current_time = datetime.strptime(days_blocks[day_idx][block_idx][2], fmt)
            num_courts = days_blocks[day_idx][block_idx][1]
            
        actual_col = start_col + relative_col_offset
        col_letter = get_column_letter(actual_col)
        
        # 1. Write Time Header
        sheet.cell(row=current_section_start_row - 1, column=actual_col).value = current_time.strftime(fmt)

        # 2. Write Matches
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
                cell.font = Font(color="000000" if text_choice == "black" else "FFFFFF")

        # 3. Add COUNTA Formula
        first_row = current_section_start_row
        last_row = current_section_start_row + num_courts - 1
        last_col_letter = get_column_letter(actual_col + 1)
        
        formula_row = last_row + 1
        formula_cell = sheet.cell(row=formula_row, column=actual_col)
        formula_cell.value = f"=COUNTA({col_letter}{first_row}:{last_col_letter}{last_row})"

        current_time += timedelta(minutes=15)
        relative_col_offset += 1
        slots_processed_in_block += 1

    book.save(file_path)
    print(f"➡️  Schedule written dynamically across {len(days_blocks)} days.")
'''
def write_schedule_to_excel(file_path, schedule, event_colors, days_blocks, sheet_name, class_names, start_row, start_col, matches):
    try:
        book = load_workbook(file_path)
    except FileNotFoundError:
        print(f"❌ Error: The file '{file_path}' was not found. Skipping writing the schedule to Excel.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    sheet_name = f"{sheet_name} {timestamp}"

    if sheet_name in book.sheetnames:
        del book[sheet_name]
    
    sheet = book.create_sheet(sheet_name)

    fmt = "%H:%M"

    current_section_start_row = start_row
    relative_col_offset = 0
    
    # NEW: Track the lowest row written to and the round times dynamically
    lowest_row_written = start_row
    class_round_times = {}  # Format: { "Class Name": { "Round Name": "HH:MM" } }

    day_idx = 0
    block_idx = 0
    slots_processed_in_block = 0

    current_time = datetime.strptime(days_blocks[day_idx][block_idx][2], fmt)
    num_courts = days_blocks[day_idx][block_idx][1]
    max_courts_current_day = max(b[1] for b in days_blocks[day_idx])

    for i in range(max_courts_current_day):
        sheet.cell(row=current_section_start_row + i, column=start_col - 1).value = i + 1

    for slot_idx, time_slot in enumerate(schedule):
        if slots_processed_in_block >= days_blocks[day_idx][block_idx][0]:
            block_idx += 1
            slots_processed_in_block = 0
            
            if block_idx >= len(days_blocks[day_idx]):
                current_section_start_row += (max_courts_current_day + 6)
                day_idx += 1
                if day_idx >= len(days_blocks):
                    break 
                
                block_idx = 0
                relative_col_offset = 0
                max_courts_current_day = max(b[1] for b in days_blocks[day_idx])
                
                for i in range(max_courts_current_day):
                    sheet.cell(row=current_section_start_row + i, column=start_col - 1).value = i + 1
                    
            current_time = datetime.strptime(days_blocks[day_idx][block_idx][2], fmt)
            num_courts = days_blocks[day_idx][block_idx][1]
            
        actual_col = start_col + relative_col_offset
        col_letter = get_column_letter(actual_col)
        time_str = current_time.strftime(fmt)
        
        # 1. Write Time Header
        sheet.cell(row=current_section_start_row - 1, column=actual_col).value = time_str

        # 2. Write Matches & Extract Round Times
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
            
            # --- EXTRACT CLASS AND ROUND TIMES HERE ---
            if "\n" in full_match_text:
                class_name, round_name = full_match_text.split("\n", 1)
            elif " -" in full_match_text:
                class_name, round_name = full_match_text.split(" -", 1)
            else:
                class_name = full_match_text
                round_name = "Match"
                
            class_name = class_name.strip()
            round_name = round_name.strip()

            if class_name not in class_round_times:
                class_round_times[class_name] = {}
            
            # Dynamically determine the day names
            total_days = len(days_blocks)
            if total_days == 3:
                day_names = ["Fri", "Sat", "Sun"]
            elif total_days == 2:
                day_names = ["Sat", "Sun"]
            elif total_days == 1:
                day_names = ["Sat"]
            else:
                day_names = [f"Day {i+1}" for i in range(total_days)]
                
            day_str = day_names[day_idx] if day_idx < len(day_names) else f"Day {day_idx + 1}"
            time_str_ampm = current_time.strftime("%I:%M %p")
            
            if round_name not in class_round_times[class_name]:
                # Initialize the dictionary to store the day and the counts for each time
                class_round_times[class_name][round_name] = {"day": day_str, "times": {}}
            
            # Increment the count of matches for this specific time slot
            if time_str_ampm not in class_round_times[class_name][round_name]["times"]:
                class_round_times[class_name][round_name]["times"][time_str_ampm] = 0
            class_round_times[class_name][round_name]["times"][time_str_ampm] += 1
            # ------------------------------------------

            if lookup_key in event_colors:
                hex_bg, text_choice = event_colors[lookup_key]
                clean_hex = hex_bg.replace("#", "")
                cell.fill = PatternFill(start_color=clean_hex, end_color=clean_hex, fill_type="solid")
                cell.font = Font(color="000000" if text_choice == "black" else "FFFFFF")

        # 3. Add COUNTA Formula
        first_row = current_section_start_row
        last_row = current_section_start_row + num_courts - 1
        last_col_letter = get_column_letter(actual_col + 1)
        
        formula_row = last_row + 1
        formula_cell = sheet.cell(row=formula_row, column=actual_col)
        formula_cell.value = f"=COUNTA({col_letter}{first_row}:{last_col_letter}{last_row})"
        
        # Track the lowest row written
        if formula_row > lowest_row_written:
            lowest_row_written = formula_row

        current_time += timedelta(minutes=15)
        relative_col_offset += 1
        slots_processed_in_block += 1


    # Write Class Round Times (5 rows below the schedule)
    # =========================================================================
    summary_start_row = lowest_row_written + 5
    
    # Write "Round 1", "Round 2" headers leaving 4 empty columns in between
    if class_round_times:
        max_rounds = max(len(rounds) for rounds in class_round_times.values())
        for i in range(1, max_rounds + 1):
            # Calculate offset: 1->1, 2->6, 3->10, etc.
            header_col_offset = ((i - 1) * 5) + 1 
            header_cell = sheet.cell(row=summary_start_row, column=start_col + header_col_offset)
            header_cell.value = f"Round {i}"
            header_cell.font = Font(bold=True)
    
    current_summary_row = summary_start_row + 1
    
    # Iterate through the provided class_names list to enforce specific ordering
    for class_name in class_names:
        if class_name in class_round_times:
            rounds = class_round_times[class_name]
            
            # Write the class name
            class_cell = sheet.cell(row=current_summary_row, column=start_col)
            class_cell.value = class_name
            
            # Color the class name based on event_colors
            if class_name in event_colors:
                hex_bg, text_choice = event_colors[class_name]
                clean_hex = hex_bg.replace("#", "")
                class_cell.fill = PatternFill(start_color=clean_hex, end_color=clean_hex, fill_type="solid")
                class_cell.font = Font(color="000000" if text_choice == "black" else "FFFFFF")
            
            # Write each round's formatted times, jumping 4 columns each time
            col_offset = 1
            for round_name, round_data in rounds.items():
                day_str = round_data["day"]
                times_dict = round_data["times"]
                
                # Combine times and counts into: "09:00 AM (2), 10:30 AM (1)"
                time_strings = [f"{t} ({count})" for t, count in times_dict.items()]
                joined_times = ", ".join(time_strings)
                
                # Final format: "Sat: 09:00 AM (2), 10:30 AM (1)"
                formatted_output = f"{day_str}: {joined_times}"
                
                sheet.cell(row=current_summary_row, column=start_col + col_offset).value = formatted_output
                col_offset += 5 # Advance by 5 to leave 4 empty columns
                
            current_summary_row += 1
    # =========================================================================

    # =========================================================================
    # Write the raw time_of_match string 5 rows below the last printed row
    raw_solution_str = f"time_of_match={str(matches)}"
    
    # current_summary_row is already 1 row past the last written summary row.
    # To place this exactly 5 rows below the last printed row, we add 4.
    target_row = current_summary_row + 4 
    
    sheet.cell(row=target_row, column=start_col).value = raw_solution_str
    # =========================================================================

    # Write the current date and time to cell A1
    sheet.cell(row=1, column=1).value = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    book.save(file_path)
    print(f"➡️  Schedule written dynamically across {len(days_blocks)} days.")


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

    instance["umpire_chairs"] = data["umpire_chairs"]

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

    instance["nof_blocks"] = data["nof_blocks"]
    instance["block_starts"] = data["block_starts"]
    instance["block_timeslots"] = data["block_timeslots"]
    instance["block_fields"] = data["block_fields"]
    instance["block_matchslots"] = data["block_matchslots"]

    instance["last_of_day1"] = data["last_of_day1"]
    instance["last_of_day0"] = data["last_of_day0"]


    instance["nof_V_classes"] = data["nof_V_classes"]
    instance["nof_single_V_classes"] = data["nof_single_V_classes"]
    instance["nof_A_classes"] = data["nof_A_classes"]
    instance["nof_B_classes"] = data["nof_B_classes"]
    instance["nof_C_classes"] = data["nof_C_classes"]
    instance["nof_junior_classes"] = data["nof_junior_classes"]
    instance["nof_rest_classes"] = data["nof_rest_classes"]

    instance["V_start"] = data["V_start"]
    instance["V_end"] = data["V_end"]
    instance["single_V_start"] = data["single_V_start"]
    instance["single_V_end"] = data["single_V_end"]
    instance["A_start"] = data["A_start"]
    instance["A_end"] = data["A_end"]
    instance["B_start"] = data["B_start"]
    instance["B_end"] = data["B_end"]
    instance["C_start"] = data["C_start"]
    instance["C_end"] = data["C_end"]
    instance["junior_start"] = data["junior_start"]
    instance["junior_end"] = data["junior_end"]
    instance["rest_start"] = data["rest_start"]
    instance["rest_end"] = data["rest_end"]


    instance["nof_V_rounds"] = data["nof_V_rounds"]
    instance["nof_single_V_rounds"] = data["nof_single_V_rounds"]
    instance["nof_A_rounds"] = data["nof_A_rounds"]
    instance["nof_B_rounds"] = data["nof_B_rounds"]
    instance["nof_C_rounds"] = data["nof_C_rounds"]
    instance["nof_junior_rounds"] = data["nof_junior_rounds"]
    instance["nof_rest_rounds"] = data["nof_rest_rounds"]

    instance["V_rounds_start"] = data["V_rounds_start"]
    instance["V_rounds_end"] = data["V_rounds_end"]
    instance["single_V_rounds_start"] = data["single_V_rounds_start"]
    instance["single_V_rounds_end"] = data["single_V_rounds_end"]
    instance["A_rounds_start"] = data["A_rounds_start"]
    instance["A_rounds_end"] = data["A_rounds_end"]
    instance["B_rounds_start"] = data["B_rounds_start"]
    instance["B_rounds_end"] = data["B_rounds_end"]
    instance["C_rounds_start"] = data["C_rounds_start"]
    instance["C_rounds_end"] = data["C_rounds_end"]
    instance["junior_rounds_start"] = data["junior_rounds_start"]
    instance["junior_rounds_end"] = data["junior_rounds_end"]
    instance["rest_rounds_start"] = data["rest_rounds_start"]
    instance["rest_rounds_end"] = data["rest_rounds_end"]


    instance["all_matches"] = set(data["matches"])
    instance["V_matches"] = set(data["V_matches"])
    instance["single_V_matches"] = set(data["single_V_matches"])
    instance["A_matches"] = set(data["A_matches"])
    instance["B_matches"] = set(data["B_matches"])
    instance["C_matches"] = set(data["C_matches"])
    instance["junior_matches"] = set(data["junior_matches"])
    instance["matches_rest"] = set(data["matches_rest"])

    instance["V_classes"] = set(data["V_classes"])
    instance["A_classes"] = set(data["A_classes"])
    instance["B_classes"] = set(data["B_classes"])
    instance["C_classes"] = set(data["C_classes"])
    instance["junior_classes"] = set(data["junior_classes"])
    instance["rest_classes"] = set(data["rest_classes"])

    instance["V_rounds"] = set(data["V_rounds"])
    instance["A_rounds"] = set(data["A_rounds"])
    instance["B_rounds"] = set(data["B_rounds"])
    instance["C_rounds"] = set(data["C_rounds"])
    instance["junior_rounds"] = set(data["junior_rounds"])
    instance["rest_rounds"] = set(data["rest_rounds"])

    instance["singles_classes"] = set(data["singles_classes"])
    instance["doubles_classes"] = set(data["doubles_classes"])
    instance["singles_rounds"] = set(data["singles_rounds"])
    instance["doubles_rounds"] = set(data["doubles_rounds"])
    instance["singles_matches"] = set(data["singles_matches"])
    instance["doubles_matches"] = set(data["doubles_matches"])

    instance["nof_matches"] = len(data["matches"])
    instance["nof_V_matches"] = len(data["V_matches"])
    instance["nof_single_V_matches"] = len(data["single_V_matches"])
    instance["nof_A_matches"] = len(data["A_matches"])
    instance["nof_B_matches"] = len(data["B_matches"])
    instance["nof_C_matches"] = len(data["C_matches"])
    instance["nof_junior_matches"] = len(data["junior_matches"])
    instance["nof_matches_rest"] = len(data["matches_rest"])

    instance["nof_singles_classes"] = len(data["singles_classes"])
    instance["nof_doubles_classes"] = len(data["doubles_classes"])
    instance["nof_singles_rounds"] = len(data["singles_rounds"])
    instance["nof_doubles_rounds"] = len(data["doubles_rounds"])
    instance["nof_singles_matches"] = len(data["singles_matches"])
    instance["nof_doubles_matches"] = len(data["doubles_matches"])
    instance["strong_collisions"] = data["strong_collisions"]
    instance["weak_collisions"] = data["weak_collisions"]
    instance["super_weak_collisions"] = data["super_weak_collisions"]

    instance["V_round_gap"] = data["V_round_gap"]
    instance["A_round_gap"] = data["A_round_gap"]
    instance["rest_round_gap"] = data["rest_round_gap"]
    instance["junior_round_gap"] = data["junior_round_gap"]

    instance["deciding_U_round_factor"] = data["deciding_U_round_factor"]
    instance["U_big_round_start_duration"] = data["U_big_round_start_duration"]
    instance["U_small_round_start_duration"] = data["U_small_round_start_duration"]

    instance["deciding_rest_round_factor"] = data["deciding_rest_round_factor"]
    instance["big_round_start_duration"] = data["big_round_start_duration"]
    instance["small_round_start_duration"] = data["small_round_start_duration"]


    instance["U_match_duration"] = data["U_match_duration"]
    instance["rest_match_duration"] = data["rest_match_duration"]

    instance["deciding_class_factor"] = data["deciding_class_factor"]
    instance["big_class_duration"] = data["big_class_duration"]
    instance["small_class_duration"] = data["small_class_duration"]

    instance["max_round_gap"] = data["max_round_gap"]

    instance["warm_values"] = [16, 16, 19, 19, 19, 19, 19, 38, 38, 38, 38, 56, 56, 68, 13, 13, 13, 13, 13, 16, 16, 16, 30, 30, 30, 30, 51, 51, 64, 33, 42, 42, 42, 42, 64, 64, 77, 22, 22, 22, 34, 34, 34, 34, 56, 56, 76, 26, 26, 46, 46, 46, 46, 46, 49, 49, 49, 60, 60, 60, 60, 72, 72, 81, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 9, 9, 9, 9, 9, 9, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 21, 21, 21, 21, 22, 22, 22, 22, 40, 40, 40, 40, 57, 57, 67, 13, 13, 13, 13, 30, 30, 30, 30, 30, 30, 30, 30, 42, 42, 42, 42, 51, 51, 62, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 53, 53, 53, 53, 53, 53, 53, 53, 63, 63, 63, 63, 78, 78, 84, 55, 55, 55, 55, 55, 55, 67, 67, 67, 67, 76, 76, 84, 26, 26, 26, 26, 26, 36, 36, 36, 36, 48, 48, 71, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 7, 7, 7, 7, 7, 7, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 22, 22, 22, 22, 22, 23, 23, 23, 40, 40, 40, 40, 56, 56, 66, 7, 7, 7, 7, 14, 14, 14, 14, 30, 30, 50, 14, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 29, 29, 44, 44, 44, 44, 44, 44, 44, 44, 50, 50, 50, 50, 60, 60, 75, 23, 45, 45, 45, 45, 45, 45, 45, 45, 59, 59, 59, 59, 65, 65, 74, 18, 18, 18, 18, 18, 18, 18, 35, 35, 35, 35, 35, 35, 35, 35, 49, 49, 49, 49, 70, 70, 81, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 7, 7, 24, 24, 24, 24, 24, 24, 24, 24, 24, 25, 25, 25, 25, 25, 25, 25, 41, 41, 41, 41, 41, 41, 41, 41, 57, 57, 57, 57, 67, 67, 84, 7, 7, 7, 7, 15, 15, 26, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 47, 47, 47, 47, 47, 47, 47, 47, 63, 63, 63, 63, 72, 72, 79, 61, 67, 67, 67, 67, 78, 78, 84, 11, 11, 11, 11, 11, 11, 20, 20, 20, 20, 33, 33, 53]



    # Solve
    last_solution = None
    result = instance.solutions(processes=8, optimisation_level=1, intermediate_solutions=True, verbose=True, statistics=True, free_search=True
                                )

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
        #print(res.status)
    else:
        #solution = result.solution[0]
        matches = last_solution.time_of_match
        print("✅ Solution found!")
        print(str(len(matches)))

        schedule = build_schedule(data["class_index"], data["round_index"], matches, list(data["event_colors"].keys()), data)
        print_in_terminal(schedule, "09:00")

        days_blocks = get_blocks_for_schedule_printing()
        write_schedule_to_excel(file_path=data["file_path"], schedule=schedule, event_colors=data["event_colors"],days_blocks=days_blocks, sheet_name="timetable", class_names=list(data["event_colors"].keys()), start_row=4, start_col=3, matches=matches)
        print("Printed to excel!")

    print("\n----Done----\n")

'''
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
#time_of_match=[19, 19, 29, 29, 36, 36, 43, 43, 93, 93, 5, 5, 5, 5, 5, 5, 33, 33, 33, 33, 33, 33, 45, 45, 45, 45, 45, 45, 55, 55, 55, 55, 55, 55, 65, 65, 65, 65, 65, 65, 71, 71, 71, 95, 95, 1, 1, 34, 34, 45, 45, 66, 66, 66, 72, 72, 13, 13, 21, 21, 27, 27, 39, 39, 39, 50, 50, 50, 60, 60, 60, 77, 77, 77, 83, 83, 83, 89, 89, 11, 11, 11, 11, 11, 37, 37, 37, 37, 37, 51, 51, 51, 51, 51, 61, 61, 61, 61, 91, 91, 97, 9, 9, 15, 15, 21, 21, 27, 27, 77, 67, 67, 73, 73, 79, 79, 7, 7, 7, 7, 7, 19, 19, 19, 19, 19, 25, 25, 25, 25, 25, 33, 33, 73, 73, 79, 43, 43, 43, 54, 54, 54, 61, 61, 61, 81, 81, 94, 23, 29, 35, 43, 43, 43, 43, 53, 53, 53, 53, 67, 67, 67, 67, 88, 88, 94, 3, 3, 16, 16, 22, 22, 24, 24, 30, 30, 41, 41, 90, 90, 96, 96, 33, 33, 44, 44, 52, 52, 59, 59, 97, 97, 7, 7, 14, 14, 20, 20, 69, 69, 79, 79, 23, 23, 23, 23, 41, 41, 41, 41, 58, 58, 58, 58, 67, 67, 84, 29, 29, 29, 35, 35, 35, 77, 77, 77, 86, 86, 92, 43, 52, 60, 32, 38, 49, 63, 63, 69, 69, 79, 79, 3, 3, 47, 47, 55, 55, 62, 62, 71, 81, 81, 87, 87, 93, 93, 11, 11, 40, 40, 65, 65, 73, 73, 81, 81, 18, 18, 26, 26, 69, 69, 77, 47, 47, 59, 59, 87, 87, 95, 5, 5, 5, 5, 5, 5, 13, 13, 13, 13, 13, 13, 21, 21, 21, 21, 21, 21, 35, 46, 46, 66, 11, 11, 11, 11, 11, 23, 23, 23, 23, 23, 35, 35, 35, 35, 35, 51, 51, 63, 29, 29, 29, 29, 41, 41, 41, 41, 56, 56, 56, 56, 83, 83, 92, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 49, 49, 49, 49, 49, 49, 49, 49, 63, 63, 63, 63, 70, 70, 80, 7, 7, 13, 13, 45, 45, 51, 51, 63, 27, 27, 27, 27, 27, 27, 28, 28, 38, 39, 39, 39, 39, 39, 39, 39, 57, 57, 57, 57, 57, 57, 57, 57, 75, 75, 75, 75, 75, 75, 75, 75, 85, 85, 85, 85, 91, 91, 97, 3, 3, 3, 3, 3, 3, 3, 3, 15, 15, 15, 15, 15, 15, 15, 15, 31, 31, 31, 31, 31, 31, 31, 32, 47, 47, 47, 47, 47, 47, 64, 64, 64, 64, 71, 71, 81, 7, 7, 7, 19, 19, 19, 31, 31, 31, 42, 42, 48, 48, 82, 25, 25, 25, 25, 25, 37, 37, 37, 37, 37, 53, 53, 53, 53, 53, 59, 59, 59, 59, 89, 89, 95]
#time_of_match=[16, 16, 19, 19, 19, 19, 19, 31, 31, 31, 31, 53, 53, 67, 13, 13, 13, 13, 13, 16, 16, 16, 28, 28, 28, 28, 51, 51, 63, 42, 63, 63, 63, 63, 79, 79, 88, 44, 44, 44, 67, 67, 67, 67, 77, 77, 88, 23, 23, 35, 35, 35, 35, 35, 38, 38, 38, 48, 48, 48, 48, 71, 71, 84, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 17, 17, 17, 19, 19, 19, 19, 19, 29, 29, 29, 29, 50, 51, 57, 1, 1, 1, 1, 13, 13, 13, 13, 13, 13, 13, 13, 19, 19, 19, 19, 28, 28, 51, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 61, 61, 61, 61, 61, 61, 61, 61, 75, 75, 75, 75, 81, 81, 87, 57, 57, 57, 57, 59, 59, 65, 65, 65, 65, 77, 77, 87, 33, 33, 33, 33, 33, 39, 39, 39, 39, 49, 49, 70, 1, 1, 5, 5, 5, 5, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 19, 21, 21, 21, 21, 21, 21, 21, 21, 21, 22, 22, 22, 22, 22, 22, 30, 30, 30, 30, 30, 30, 30, 30, 50, 50, 50, 50, 58, 58, 64, 1, 1, 1, 1, 7, 7, 7, 7, 13, 13, 19, 14, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 26, 34, 34, 34, 34, 34, 34, 34, 34, 48, 48, 48, 49, 72, 72, 78, 31, 47, 47, 47, 47, 47, 47, 47, 47, 63, 63, 63, 63, 73, 73, 79, 39, 39, 39, 39, 39, 39, 39, 54, 54, 54, 54, 54, 54, 54, 54, 68, 68, 68, 68, 84, 84, 90, 1, 1, 1, 1, 3, 3, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 17, 17, 17, 17, 17, 17, 17, 17, 23, 23, 23, 23, 31, 31, 51, 15, 15, 15, 15, 22, 24, 31, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 45, 45, 45, 45, 45, 45, 45, 45, 61, 61, 61, 61, 75, 75, 82, 35, 45, 45, 45, 45, 51, 51, 71, 41, 41, 41, 41, 41, 41, 56, 56, 56, 56, 66, 66, 86]
time_of_match=[16, 16, 19, 19, 19, 19, 19, 38, 38, 38, 38, 56, 56, 68, 13, 13, 13, 13, 13, 16, 16, 16, 30, 30, 30, 30, 51, 51, 64, 33, 42, 42, 42, 42, 64, 64, 77, 22, 22, 22, 34, 34, 34, 34, 56, 56, 76, 26, 26, 46, 46, 46, 46, 46, 49, 49, 49, 60, 60, 60, 60, 72, 72, 81, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 9, 9, 9, 9, 9, 9, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 21, 21, 21, 21, 22, 22, 22, 22, 40, 40, 40, 40, 57, 57, 67, 13, 13, 13, 13, 30, 30, 30, 30, 30, 30, 30, 30, 42, 42, 42, 42, 51, 51, 62, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 53, 53, 53, 53, 53, 53, 53, 53, 63, 63, 63, 63, 78, 78, 84, 55, 55, 55, 55, 55, 55, 67, 67, 67, 67, 76, 76, 84, 26, 26, 26, 26, 26, 36, 36, 36, 36, 48, 48, 71, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 7, 7, 7, 7, 7, 7, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 22, 22, 22, 22, 22, 23, 23, 23, 40, 40, 40, 40, 56, 56, 66, 7, 7, 7, 7, 14, 14, 14, 14, 30, 30, 39, 14, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 29, 29, 44, 44, 44, 44, 44, 44, 44, 44, 50, 50, 50, 50, 60, 60, 75, 23, 45, 45, 45, 45, 45, 45, 45, 45, 59, 59, 59, 59, 65, 65, 74, 18, 18, 18, 18, 18, 18, 18, 35, 35, 35, 35, 35, 35, 35, 35, 49, 49, 49, 49, 70, 70, 81, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 7, 7, 24, 24, 24, 24, 24, 24, 24, 24, 24, 25, 25, 25, 25, 25, 25, 25, 41, 41, 41, 41, 41, 41, 41, 41, 57, 57, 57, 57, 67, 67, 84, 7, 7, 7, 7, 15, 15, 26, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 37, 47, 47, 47, 47, 47, 47, 47, 47, 63, 63, 63, 63, 72, 72, 79, 61, 67, 67, 67, 67, 78, 78, 84, 11, 11, 11, 11, 11, 11, 20, 20, 20, 20, 33, 33, 53]
schedule = build_schedule(data["class_index"], data["round_index"], time_of_match, list(data["event_colors"].keys()), data)
print("TIMESLOTS:")

print_in_terminal(schedule, "09:00")

print(f"Total matches from minizinc: {str(len(time_of_match))}")
total_matches = sum(1 for slot in schedule for match in slot if match.strip())
print(f"Total matches in schedule: {total_matches}")

days_blocks = get_blocks_for_schedule_printing()
write_schedule_to_excel(file_path=data["file_path"], schedule=schedule, event_colors=data["event_colors"],days_blocks=days_blocks, sheet_name="timetable", class_names=list(data["event_colors"].keys()), start_row=4, start_col=3, matches=time_of_match)
#write_schedule_to_excel(data["file_path"], schedule, data["event_colors"], "18:00", sheet_name="timetable", start_row=4, start_col=3)
#write_schedule_to_excel(data["file_path"], schedule, sheet_name="timetable", start_row=4, start_col=4)

print("\n----Done----\n")
