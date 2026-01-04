import pandas as pd
from collections import defaultdict, Counter
import math
from openpyxl import load_workbook
from datetime import datetime, timedelta
from openpyxl.utils import get_column_letter

def parse_competition_excel(file_path, event_codes):
    # Read Excel (no header, since layout is irregular)
    df = pd.read_excel(file_path, header=None, usecols="A:D")
    
    event_players = defaultdict(set)   # event -> set of players
    player_events = defaultdict(set)   # player -> set of events

    current_event = None
    current_player = None

    for idx, row in df.iterrows():
        col_a, _, col_c, col_d = row[0], row[1], row[2], row[3]

        # Detect event in column A
        if pd.notna(col_a):
            cell_text = str(col_a).strip()
            if cell_text.lower().endswith("main draw"):     # we ignore all events that are not the main draw
                words = str(col_a)[11:].split()
                current_event = " ".join(words[:2])
                current_player = None
            else:
                current_event = None
            continue

        # Detect player name in column C
        if pd.notna(col_c):

            if str(col_c).strip().lower() == "name":
                current_player = None
                continue
            if str(col_c).strip().lower() == "<partner wanted>":
                current_player = None
                continue

            current_player = str(col_c).strip()
            if current_event:
                event_players[current_event].add(current_player)
                player_events[current_player].add(current_event)

    # Build cross-event participation summary
    event_correlations = {}
    for event, players in event_players.items():
        counter = Counter()
        for player in players:
            for other_event in player_events[player]:
                if other_event != event:
                    counter[other_event] += 1
        event_correlations[event] = list(counter.items())

    return event_correlations, event_players, player_events

def analyze_collisions(event_correlations):
    strong_collision = {}
    weak_collision = {}
    super_weak_collision = {}

    for event, correlations in event_correlations.items():
        event_suffix = event[-1] if event else ""
        same = []
        different_1 = []
        different_2 = []

        for other_event, count in correlations:
            other_suffix = other_event[-1] if other_event else ""
            if other_suffix == event_suffix:
                same.append(other_event)
            else:
                if count > 2:
                    different_1.append((other_event, count))
                else:
                    different_2.append((other_event, count))


        strong_collision[event] = same
        weak_collision[event] = different_1
        super_weak_collision[event] = different_2

    return strong_collision, weak_collision, super_weak_collision

def calculate_tournament_structure(event_players):
    event_structures = {}
    round_schedules = {}

    for event, players in event_players.items():
        player_count = len(players)
        event_type = event[1].upper() if len(event) > 1 else "S"
        participants = player_count // (2 if event_type == "D" else 1)

        if participants <= 1:
            event_structures[event] = {"round_robin": [], "elimination": [], "lower_playoff": []}
            round_schedules[event] = []
            continue

        # --- 1. Partition into Round Robin Groups ---
        if participants <= 5:
            groups = [participants]
        else:
            best_groups = None
            min_matches = float('inf')
            for y in range((participants // 4) + 1):
                rem = participants - (y * 4)
                if rem >= 0 and rem % 3 == 0:
                    x = rem // 3
                    total_m = (x * 3) + (y * 6)
                    if total_m < min_matches:
                        min_matches = total_m
                        best_groups = [3] * x + [4] * y
            groups = best_groups

        # --- 2. RR Matches per Round ---
        rr_rounds = []
        max_rr_rounds = max((g if g % 2 != 0 else g - 1) for g in groups)
        for r in range(max_rr_rounds):
            m = sum(g // 2 for g in groups if r < (g if g % 2 != 0 else g - 1))
            rr_rounds.append(m)

        # --- 3. Elimination Rounds Logic ---
        upper_elim = []
        lower_elim = []
        
        if participants > 5:
            # Determine how many advance based on Class (A or V)
            # We look for A or V at the end of the event name or specific class markers
            is_elite_class = any(cls in event for cls in [" A", " V"])

            is_bronze_event = any(event.endswith(s) for s in ["9", "11", "13"])
            
            # Upper: Top 1 for Elite and A (A/V), Top 2 for others
            advancing_per_group = 1 if is_elite_class else 2
            upper_count = len(groups) * advancing_per_group

            # Calculate Upper Elim (including Bronze match if applicable)
            upper_elim = self_calculate_elim(upper_count, has_bronze=is_bronze_event)

            # Lower: Everyone else (only if event ends in 9, 11, or 13)
            if is_bronze_event:
                lower_count = participants - upper_count
                if lower_count > 1:
                    lower_elim = self_calculate_elim(lower_count)

        # --- 4. Merge Playoff Rounds (Simultaneous Play) ---
        playoff_rounds = []
        num_playoff_rounds = max(len(upper_elim), len(lower_elim))
        
        for i in range(num_playoff_rounds):
            m_upper = upper_elim[i] if i < len(upper_elim) else 0
            m_lower = lower_elim[i] if i < len(lower_elim) else 0
            playoff_rounds.append(m_upper + m_lower)

        # --- 5. Package Results ---
        event_structures[event] = {
            "round_robin": groups,
            "elimination": upper_elim,
            "lower_playoff": lower_elim
        }
        round_schedules[event] = rr_rounds + playoff_rounds

    return event_structures, round_schedules

def self_calculate_elim(n, has_bronze=False):
    """Calculates elimination matches, adding 1 to the final round for Bronze match."""
    if n <= 1: return []
    rounds = []
    x = math.ceil(math.log2(n))
    
    # First round (Play-ins)
    if 2**x == (n / 2):
        first = int(2**x)
    else:
        first = int(n - 2**(x - 1))
    rounds.append(first)
    
    # Subsequent rounds
    matches = 2 ** (x - 2)
    while matches >= 1:
        rounds.append(matches)
        matches //= 2
    
    # Add Bronze Match: If has_bronze is True and there were at least 4 players 
    # (semi-finals), add +1 to the very last round (the Final).
    if has_bronze and n >= 4 and len(rounds) > 0:
        rounds[-1] += 1
        
    return rounds



def check_rule_violations(player_events):
    warnings = []

    for player, events in player_events.items():
        events = list(events)

        # Rule 1: If playing a V event, no other event with same prefix
        '''
        v_prefixes = {e[:2] for e in events if e.endswith("V")}
        for prefix in v_prefixes:
            conflicting = [e for e in events if e.startswith(prefix) and not e.endswith("V")]
            if conflicting:
                warnings.append(
                    f"⚠️ {player}: plays {', '.join([e for e in events if e.startswith(prefix) and e.endswith('V')])}, "
                    f"so cannot play {', '.join(conflicting)}"
                )
        '''

        # Rule 2: No more than 3 total events
        if len(events) > 3:
            warnings.append(f"⚠️ {player}: participates in {len(events)} events ({', '.join(events)})")

        # Rule 3: No more than two non-V events with same prefix
        '''
        non_v_events = [e for e in events if not e.endswith("V")]
        prefix_counts = {}
        for e in non_v_events:
            prefix = e[:2]
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

        for prefix, count in prefix_counts.items():
            if count > 2:
                same_prefix_events = [e for e in non_v_events if e.startswith(prefix)]
                warnings.append(
                    f"⚠️ {player}: plays {count} events with prefix '{prefix}' ({', '.join(same_prefix_events)})"
                )
        '''

        # Rule 4: No 3+ events with second character D
        '''
        d_class_events = [e for e in events if len(e) > 1 and e[1].upper() == "D"]
        if len(d_class_events) >= 3:
            warnings.append(
                f"⚠️ {player}: plays {len(d_class_events)} doubles classes ({', '.join(d_class_events)})"
            )
        '''

    return warnings

def find_problematic_players(player_events, event_players, event_correlations):
    problematic_players = {}
    checked_pairs = set()  # to avoid duplicate collision reports
    
    # Sole collision cause
    for event, collisions in event_correlations.items():
        for other_event, _ in collisions:
            # Normalize pair so ("MS V", "XD A") == ("XD A", "MS V")
            pair_key = tuple(sorted([event, other_event]))
            if pair_key in checked_pairs:
                continue  # skip duplicate
            checked_pairs.add(pair_key)

            players_in_both = event_players.get(event, set()) & event_players.get(other_event, set())

            if len(players_in_both) == 1:
                sole_player = next(iter(players_in_both))
                problematic_players.setdefault(sole_player, []).append(
                    f"Sole reason {pair_key[0]} collides with {pair_key[1]}"
                )


    return problematic_players

def write_player_events_to_excel(file_path, player_events, problematic_players, sheet_name="Player Events"):
    """
    Adds/updates a sheet listing all players, their events, and warning reasons if they're problematic.
    """

    book = load_workbook(file_path)

    # Create sheet if missing
    if sheet_name not in book.sheetnames:
        sheet = book.create_sheet(sheet_name)
        headers = ["Player", "Events", "Warnings"]
        sheet.append(headers)

    sheet = book[sheet_name]

    # Clear only the data area (keep headers & formatting)
    for row in sheet.iter_rows(min_row=2, max_col= 3):
        for cell in row:
            cell.value = None

    # Write new data
    current_row = 2
    for player, events in sorted(player_events.items()):
        events_str = ", ".join(sorted(events))
        if player in problematic_players:
            reasons = " ⚠️ " + " | ⚠️ ".join(problematic_players[player])
        else:
            reasons = ""
        sheet.cell(row=current_row, column=1).value = player
        sheet.cell(row=current_row, column=2).value = events_str
        sheet.cell(row=current_row, column=3).value = reasons

        current_row += 1

    book.save(file_path)

    print(f"✅ Added players to '{sheet_name}' in {file_path}")



def write_event_analysis_to_excel(file_path, event_correlations, round_schedules, event_structures, event_players, sheet_name="Event Analysis"):
    """
    Updates the analysis sheet with a gap column and the RR/Elim/Lower 
    elements joined by ", " (no brackets).
    """
    
    # 1. Calculate the layout based on max rounds
    max_rounds = 0
    if round_schedules:
        max_rounds = max(len(rounds) for rounds in round_schedules.values())
    
    # Define Column Indices
    # Gap is at 4 + max_rounds
    rr_col = 5 + max_rounds
    elim_col = 6 + max_rounds
    lower_col = 7 + max_rounds

    book = load_workbook(file_path)
    if sheet_name not in book.sheetnames:
        sheet = book.create_sheet(sheet_name)
    else:
        sheet = book[sheet_name]

    # 2. Write Headers
    headers_base = ["Event", "Collides With", "Player amount"]
    round_headers = [f"Round {i+1}" for i in range(max_rounds)]
    
    for i, h in enumerate(headers_base + round_headers, 1):
        sheet.cell(row=1, column=i).value = h
    
    sheet.cell(row=1, column=rr_col).value = "RR"
    sheet.cell(row=1, column=elim_col).value = "Elim"
    sheet.cell(row=1, column=lower_col).value = "Lower"

    # 3. Clear data area (up to the last new column)
    for row in sheet.iter_rows(min_row=2, max_col=lower_col):
        for cell in row:
            cell.value = None

    # 4. Write new data
    current_row = 2
    for event, collisions in event_correlations.items():
        sheet.cell(row=current_row, column=1).value = event
        sheet.cell(row=current_row, column=2).value = ", ".join(
            [f"{other} ({count})" for other, count in collisions]
        )
        sheet.cell(row=current_row, column=3).value = len(event_players.get(event, []))

        # Round match counts
        rounds = round_schedules.get(event, [])
        for i, match_count in enumerate(rounds):
            sheet.cell(row=current_row, column=4 + i).value = match_count

        # Structure columns with custom formatting (no brackets)
        if event in event_structures:
            struct = event_structures[event]
            
            # Helper to join elements by ", " instead of str(list)
            def fmt_list(lst):
                return ", ".join(map(str, lst)) if lst else ""

            sheet.cell(row=current_row, column=rr_col).value = fmt_list(struct.get("round_robin"))
            sheet.cell(row=current_row, column=elim_col).value = fmt_list(struct.get("elimination"))
            sheet.cell(row=current_row, column=lower_col).value = fmt_list(struct.get("lower_playoff"))

        current_row += 1
    
    book.save(file_path)
    print(f"✅ Analysis updated. Data formatted as requested (no brackets).")

def log_rule_violations_to_excel(file_path, rule_violations, sheet_name="Rule Violations"):
    """
    Logs rule violations to a persistent sheet.
    Keeps all previous data and adds timestamped sections.
    """

    book = load_workbook(file_path)

    # Create sheet if missing
    if sheet_name not in book.sheetnames:
        sheet = book.create_sheet(sheet_name)
        sheet.append(["Date/Time", "Player", "Violation"])
    else:
        sheet = book[sheet_name]

    # Find first empty row
    next_row = sheet.max_row + 2  # leave a blank line
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.cell(row=next_row, column=1).value = f"Log entry at {timestamp}"
    next_row += 1

    # Write violations
    for v in rule_violations:
        player, description = v.split(":", 1) if ":" in v else ("Unknown", v)
        sheet.cell(row=next_row, column=2).value = player.strip()
        sheet.cell(row=next_row, column=3).value = description.strip()
        next_row += 1

    book.save(file_path)
    print(f"✅ Appended {len(rule_violations)} rule violations to '{sheet_name}' in {file_path}")

def half_hour_slots(start_datetime: str, end_datetime: str):
    """
    Calculates how many 30-minute slots fit between two times (HH:MM format).
    Returns an integer count.
    """
    datetime_format = "%Y-%m-%d %H:%M"
    start = datetime.strptime(start_datetime, datetime_format)
    end = datetime.strptime(end_datetime, datetime_format)
    
    if end <= start:
        raise ValueError("End time must be after start time.")
    
    # Calculate total minutes difference
    slot_length = timedelta(minutes=30)
    
    count = 0
    current = start
    while current <= end:
        count += 1
        current += slot_length
    
    return count

def minizinc_data(print_lists = True):

    file_path = "Entries Dubbelturnering 2026 1.1.xlsx"  # <-- Excel file
    event_codes = {"W", "M", "X", "B", "G"}
    event_correlations, event_players, player_events = parse_competition_excel(file_path, event_codes)
    strong_collision, weak_collision, super_weak_collision = analyze_collisions(event_correlations)
    event_structures, round_schedules = calculate_tournament_structure(event_players)

    # Time slots that can hold matches (15 min)
    day_zero = half_hour_slots("2025-10-10 18:00", "2025-10-10 21:00") * 2 - 1
    day_one = half_hour_slots("2025-10-10 09:00", "2025-10-10 21:00") * 2 - 1
    day_two_1 = half_hour_slots("2025-10-10 09:00", "2025-10-10 10:00") * 2 - 1
    day_two_2 = half_hour_slots("2025-10-10 10:30", "2025-10-10 14:00") * 2 - 1
    day_two_3 = half_hour_slots("2025-10-10 14:30", "2025-10-10 19:00") * 2 - 1

    # The tree different time slots based on how many fields are available
    timeslots_12_fields = day_zero + day_one + day_two_1
    timeslots_8_fields = day_two_2
    timeslots_6_fields = day_two_3

    # amount of fields
    fields_1 = 12
    fields_2 = 8
    fields_3 = 6

    # amount of matchslots
    matchslots_1 = timeslots_12_fields * fields_1
    matchslots_2 = timeslots_8_fields * fields_2
    matchslots_3 = timeslots_6_fields * fields_3

    # the last slots of day 0 and first of day 1
    last_of_day0 = day_zero
    last_of_day1 = (day_zero + day_one)
    

    # 2d list where index is class and element is list of matches (size = rounds)
    elimination_data_minizinc = [i[1] for i in round_schedules.items()]

    event_number_dict = {i[1]: i[0] + 1 for i in enumerate(round_schedules.keys())}

    number_event_dict = {x[1]: x[0] for x in event_number_dict.items()}

    print("CLASS NUMBERS:")
    print(number_event_dict, end="\n\n")

    event_to_number = lambda x: event_number_dict[x]

    # collisions paired up
    seen_pairs = set()
    strong_collision_minizinc = []

    for i, (_, values) in enumerate(strong_collision.items()):
        for v in values:
            a = i + 1
            b = event_to_number(v)
            key = tuple(sorted((a, b)))  # Ensure (1,2) and (2,1) are treated the same
            if key not in seen_pairs:
                seen_pairs.add(key)
                strong_collision_minizinc.extend([a, b])
    
    seen_pairs = set()
    weak_collision_minizinc = []
    for i, (_, values) in enumerate(weak_collision.items()):
        for v in values:
            a = i + 1
            b = event_to_number(v[0])   # v is a tuple of event name and amount of colliding players
            key = tuple(sorted((a, b)))
            if key not in seen_pairs:
                seen_pairs.add(key)
                weak_collision_minizinc.extend([a, b])
    
    seen_pairs = set()
    super_weak_collision_minizinc = []
    for i, (_, values) in enumerate(super_weak_collision.items()):
        for v in values:
            a = i + 1
            b = event_to_number(v[0])   # v is a tuple of event name and amount of colliding players
            key = tuple(sorted((a, b)))
            if key not in seen_pairs:
                seen_pairs.add(key)
                super_weak_collision_minizinc.extend([a, b])


    matches_minizic = []
    V_matches = []
    A_matches = []
    junior_matches = []
    matches_rest = []
    is_elite_match = False
    is_A_match = False
    is_junior_match = False
    class_index = []
    round_index = []
    first_singles_round_M = []
    first_doubles_mixt_round_M = []
    first_singles_round_W = []
    first_doubles_mixt_round_W = []

    # fix so it counts!!!
    # start_of_V_classes = 0 good to have later
    nof_V_classes = 0
    nof_A_classes = 0
    nof_junior_classes = 0
    nof_rest_classes = 0

    
    # Iterate through the event names in the event_players dictionary
    for event_name in event_players.keys():
        # 1. Check for V classes (ending with V)
        if event_name.endswith("V"):
            nof_V_classes += 1
            
        # 2. Check for A classes (ending with A)
        elif event_name.endswith("A"):
            nof_A_classes += 1
            
        # 3. Check for Junior classes (containing U9, U11, or U13)
        # Using 'in' is safer here in case the name is 'BS U13' or 'BS U13 '
        elif any(jr in event_name for jr in ["U9", "U11", "U13"]):
            nof_junior_classes += 1
            
        # 4. Everything else
        else:
            nof_rest_classes += 1
    

    # Initialize index trackers for when the special classes start and end
    V_range = {"start": 0, "end": 0}
    A_range = {"start": 0, "end": 0}
    junior_range = {"start": 0, "end": 0}

    # Initialize index trackers for when the special rounds start and end
    V_rounds_range = {"start": 0, "end": 0}
    A_rounds_range = {"start": 0, "end": 0}
    junior_rounds_range = {"start": 0, "end": 0}

    count = 1
    class_nr = 1
    round_counter = 1
    

    for outer in elimination_data_minizinc:
        is_elite_match = False
        is_A_match = False
        is_junior_match = False

        class_index.append(count)

        current_event_name = number_event_dict[class_nr]

        if current_event_name.endswith("V"):
            is_elite_match = True
            if V_range["start"] == 0: V_range["start"] = class_nr
            V_range["end"] = class_nr

        elif current_event_name.endswith("A"):
            is_A_match = True
            if A_range["start"] == 0: A_range["start"] = class_nr
            A_range["end"] = class_nr

        elif any(current_event_name.endswith(s) for s in ["9", "11", "13"]):
            is_junior_match = True
            if junior_range["start"] == 0: junior_range["start"] = class_nr
            junior_range["end"] = class_nr
        
        for inner in outer:
            # --- Round Tracking Logic ---
            if is_elite_match:
                if V_rounds_range["start"] == 0: V_rounds_range["start"] = round_counter
                V_rounds_range["end"] = round_counter
            elif is_A_match:
                if A_rounds_range["start"] == 0: A_rounds_range["start"] = round_counter
                A_rounds_range["end"] = round_counter
            elif is_junior_match:
                if junior_rounds_range["start"] == 0: junior_rounds_range["start"] = round_counter
                junior_rounds_range["end"] = round_counter

            round_counter += 1

            round_index.append(count)
            for _ in range(0, inner):
                if is_elite_match:
                    V_matches.append(count)
                elif is_A_match:
                    A_matches.append(count)
                elif is_junior_match:
                    junior_matches.append(count)
                else:
                    matches_rest.append(count)
                matches_minizic.append(count)
                count += 1
        class_nr += 1

    # --- Validation Logic ---
    # Helper to validate: (end - start + 1) should equal the count we found earlier
    validations = [
        ("V", V_range, nof_V_classes),
        ("A", A_range, nof_A_classes),
        ("Junior", junior_range, nof_junior_classes)
    ]

    for label, r, expected in validations:
        actual = (r["end"] - r["start"] + 1) if r["start"] != 0 else 0
        if actual != expected:
            print(f"⚠️  WARNING: {label} class mismatch! Range {r['start']}-{r['end']} "
                f"suggests {actual} classes, but {expected} were expected.")
    # --- Validation Logic ---
    
    # number of rounds for the special classes
    nof_junior_rounds = sum(len(arr) for arr in elimination_data_minizinc[junior_range["start"]-1 : junior_range["end"]])
    nof_V_rounds = sum(len(arr) for arr in elimination_data_minizinc[V_range["start"]-1 : V_range["end"]])
    nof_A_rounds = sum(len(arr) for arr in elimination_data_minizinc[A_range["start"]-1 : A_range["end"]])
    
    if print_lists:
        print("TIMESLOTS:")
        print(timeslots_12_fields, end='\n')
        print(timeslots_8_fields, end='\n')
        print(timeslots_6_fields, end='\n\n')

        print("NUMBER OF V EVENTS:")
        print(nof_V_classes, end='\n')
        print("NUMBER OF A EVENTS:")
        print(nof_A_classes, end='\n')
        print("NUMBER OF JUNIOR (U9, U11, U13) EVENTS:")
        print(nof_junior_classes, end='\n')
        print("NUMBER OF REMAINING EVENTS:")
        print(nof_rest_classes, end='\n\n')

        print("NUMBER OF V ROUNDS:")
        print(nof_V_rounds, end='\n')
        print("NUMBER OF A ROUNDS:")
        print(nof_A_rounds, end='\n')
        print("NUMBER OF JUNIOR (U9, U11, U13) ROUNDS:")
        print(nof_junior_rounds, end='\n\n')

        print("\n\n")

        print("ELIMINATION DATA:")
        print(elimination_data_minizinc, end='\n\n')
        print("CLASS INDEXES:")
        print(class_index, end='\n\n')
        print("ROUND INDEXES:")
        print(round_index, end='\n\n')
        print("MATCHES:")
        print(matches_minizic, end='\n\n')
        #print("UMPIRE MATCHES:")
        #print(umpire_matches, end='\n\n')
        #print("MATCHES WITHOUT UMPIRE MATCHES:")
        #print(matches_no_umpire, end='\n\n')
        print("STRONG COLLISION:")
        print(strong_collision, end='\n\n')
        print("STRONG COLLISION MINIZINC:")
        print(strong_collision_minizinc, end="\n\n")
        print("WEAK COLLISION:")
        print(weak_collision, end="\n\n")
        print("WEAK COLLISION MINIZINC:")
        print(weak_collision_minizinc, end="\n\n")
        print("SUPER WEAK COLLISION:")
        print(super_weak_collision, end="\n\n")
        print("SUPER WEAK COLLISION MINIZINC:")
        print(super_weak_collision_minizinc, end="\n\n")
        #print("AMOUNT OF ELITE ROUNDS")
        #print(nof_elit_rounds, end="\n\n")

    data = {
        "file_path": file_path,

        "strong_collision": strong_collision_minizinc,
        "weak_collision": weak_collision_minizinc,
        "super_weak_collision": super_weak_collision_minizinc,

        "class_index": class_index,
        "round_index": round_index,

        "timeslots_12_fields": timeslots_12_fields,
        "timeslots_8_fields": timeslots_8_fields,
        "timeslots_6_fields": timeslots_6_fields,

        "fields_1": fields_1,
        "fields_2": fields_2,
        "fields_3": fields_3,

        "matchslots_1": matchslots_1,
        "matchslots_2": matchslots_2,
        "matchslots_3": matchslots_3,

        "last_of_day1": last_of_day1,
        "last_of_day0": last_of_day0,

        "nof_V_classes": nof_V_classes,
        "nof_A_classes": nof_A_classes,
        "nof_junior_classes": nof_junior_classes,

        "V_start": V_range["start"],
        "V_end": V_range["end"],
        "A_start": A_range["start"],
        "A_end": A_range["end"],
        "junior_start": junior_range["start"],
        "junior_end": junior_range["end"],

        "nof_V_rounds": nof_V_rounds,
        "nof_A_rounds": nof_A_rounds,
        "nof_junior_rounds": nof_junior_rounds,

        "V_rounds_start": V_rounds_range["start"],
        "V_rounds_end": V_rounds_range["end"],
        "A_rounds_start": A_rounds_range["start"],
        "A_rounds_end": A_rounds_range["end"],
        "junior_rounds_start": junior_rounds_range["start"],
        "junior_rounds_end": junior_rounds_range["end"],
        
        "matches": matches_minizic,
        "V_matches": V_matches,
        "A_matches": A_matches,
        "junior_matches": junior_matches,
        "matches_rest": matches_rest,
    }

    return data

def main():
    file_path = "Entries Dubbelturnering 2026 1.1.xlsx"  # <-- your Excel file
    event_codes = {"W", "M", "X", "B", "G"}
    event_correlations, event_players, player_events = parse_competition_excel(file_path, event_codes)
    strong_collision, weak_collision, super_weak_collision = analyze_collisions(event_correlations)
    event_structures, round_schedules = calculate_tournament_structure(event_players)
    rule_violations = check_rule_violations(player_events)
    problematic_players = find_problematic_players(player_events, event_players, event_correlations)
    #write_player_events_to_excel(file_path, player_events, problematic_players, sheet_name="Player Events")
    #write_event_analysis_to_excel(file_path, event_correlations, round_schedules, event_structures, event_players, sheet_name="Event Analysis")
    #log_rule_violations_to_excel(file_path, rule_violations, sheet_name="Rule Violations")
    time_slots = half_hour_slots("2025-10-10 09:00", "2025-10-10 13:30")

    day_zero = half_hour_slots("2025-10-10 18:00", "2025-10-10 21:00") * 2 - 1
    day_one = half_hour_slots("2025-10-10 09:00", "2025-10-10 21:00") * 2 - 1
    day_two_1 = half_hour_slots("2025-10-10 09:00", "2025-10-10 10:00") * 2 - 1
    day_two_2 = half_hour_slots("2025-10-10 10:30", "2025-10-10 14:00") * 2 - 1
    day_two_3 = half_hour_slots("2025-10-10 14:30", "2025-10-10 15:00") * 2 - 1

    print(str(day_zero))
    print(str(day_one))
    print(str(day_two_1))
    print(str(day_two_2))
    print(str(day_two_3))
    

    #print(str(time_slots))

    # Print all players for all events
    
    print("\n=== Event -> Players ===")
    for event, players in event_players.items():
        print(f"{event}: {sorted(players)}")
    
    # Print the amount of entries for all events
    '''
    print("\n=== Event -> num Players ===")
    for event, participants in participants_structure.items():
        print(f"{event}: {participants}")
    '''
    # Print all events for all player
    '''
    print("\n=== Player -> Events ===")
    for player, events in player_events.items():
        print(f"{player}: {sorted(events)}")
    '''
    # Print all collitions for an event (with wight)
    '''
    print("\n=== Event Correlations ===")
    for event, correlations in event_correlations.items():
        print(f"\nEvent: {event}")
        for other_event, count in correlations:
            print(f"  {other_event}: {count}")
    '''
    # Print strong collisions for an event
    '''
    print("\n=== Events colliding with same last character ===")
    for event, others in strong_collision.items():
        print(f"{event}: {others}")
    '''
    # Print weak collitions for an event (with wight)
    '''
    print("\n=== Events colliding with different last character (with counts) ===")
    for event, others in weak_collision.items():
        print(f"{event}: {others}")
    '''
    # Print mathces per elimination round per event
    '''
    print("\n=== Event structures ===")
    for event, rounds in event_structures.items():
        print(f"{event}: {rounds}")
    
    print("\n=== Rounds and matches per round ===")
    for event, rounds in round_schedules.items():
        print(f"{event}: {rounds}")
    '''
    
    # Print warnings related to players entries
    '''
    for warning in rule_violations:
        print(warning)
    '''
    # Print summary
    '''
    print("\n=== Problematic Players ===")
    if not problematic_players:
        print("✅ No problematic players found.")
    else:
        for player, reasons in problematic_players.items():
            print(f"⚠️ {player}:")
            for reason in reasons:
                print(f"   - {reason}")
    '''

if __name__ == "__main__":
    #minizinc_data()
    main()