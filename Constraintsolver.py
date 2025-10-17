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


def build_schedule(class_index, round_index, matches, class_names, data):
    # Find how many time slots exist
    num_groups = data["timeslots"]  # assuming time slots start at 0

    # Initialize 2D list of None values (each slot has 10 possible matches)
    schedule = [["        " for _ in range(data["fields"])] for _ in range(num_groups)]

    # Track how many matches are already in each time slot
    slot_counts = [0] * num_groups

    # Go through each match
    for match_index, time_slot in enumerate(matches):
        # Find current count for this slot
        group_slot = (time_slot - 1) // data["fields"]  # group every 10 slots together
        count = slot_counts[group_slot]
        
        match_index_plus_one = match_index + 1     # since matches index starts with 1
        # Only place if there’s still space
        if count < data["fields"]:
            class_id = find_class(match_index_plus_one, class_index)
            round_id = find_round(match_index_plus_one, class_index, round_index)
            schedule[group_slot][count] = f"{class_names[class_id - 1]} - {round_id}"
            slot_counts[group_slot] += 1
        else:
            # Optional: warn if slot overflows
            print(f"Warning: time slot {time_slot} already full")

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
            if match is None:
                continue

            # Write match
            cell = sheet.cell(row=row_idx, column=col_idx)
            cell.value = match

            # Determine class prefix
            class_prefix = match[:4]

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




async def main():
    # Load model
    model = minizinc.Model("model.mzn")

    data = minizinc_data()



    # Choose solver (you can replace "gecode" with another installed solver)
    solver = minizinc.Solver.lookup("chuffed")
    #solver = minizinc.Solver.lookup("gecode")

    # Create instance and give input
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

    



    # Solve
    #result = instance.solve(nr_solutions=1, processes=1, optimisation_level=1)
    result = instance.solutions(processes=1, optimisation_level=3, intermediate_solutions=True, verbose=True, statistics=True, profile=True)

    last_solution = None
    async for res in result:

        # Access output
        print("\n\nRESULT:")
        print(res.statistics)
        print(res.solution, end="\n\n")

        if res.solution is None:
            continue
        else:
            schedule = build_schedule(data["class_index"], data["round_index"], res.solution.matches, class_names, data)
            print("TIMESLOTS:")
            for i, slot in enumerate(schedule):
                if i < 10:
                    print(f"Time slot {i}:  ", end=" | ")
                else:
                    print(f"Time slot {i}: ", end=" | ")
                for match in slot:
                    print(match, end=" | ")
                print("")

            last_solution = res.solution



    #solution = result[0]
    #matches = solution.matches

    if last_solution is None or len(last_solution) == 0:
        print("❌ No solution found.")
    else:
        solution = result.solution[0]
        matches = solution.matches
        print("✅ Solution found!")

        schedule = build_schedule(data["class_index"], data["round_index"], matches, class_names, data)
        print("TIMESLOTS:")
        for i, slot in enumerate(schedule):
            print(f"Time slot {i}: {slot}")

        write_schedule_to_excel(data["file_path"], schedule, colors)

asyncio.run(main())
