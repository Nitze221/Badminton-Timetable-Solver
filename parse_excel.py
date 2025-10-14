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
                current_event = str(col_a)[11:15].strip()
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

        # Detect player’s events in column D
        if pd.notna(col_d) and current_player:

            if str(col_d).strip().lower() == "[withdrawn]":
                continue

            event_code = str(col_d)[:4].strip()
            if event_code and event_code[0].upper() in event_codes:
                player_events[current_player].add(event_code)

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

    for event, correlations in event_correlations.items():
        event_suffix = event[-1] if event else ""
        same = []
        different = []

        for other_event, count in correlations:
            other_suffix = other_event[-1] if other_event else ""
            if other_suffix == event_suffix:
                same.append(other_event)
            else:
                different.append((other_event, count))

        strong_collision[event] = same
        weak_collision[event] = different

    return strong_collision, weak_collision

def calculate_elimination_rounds(event_players):
    elimination_structure = {}
    participants_structure = {}

    for event, players in event_players.items():
        player_count = len(players)
        if player_count == 0:
            continue

        # Determine singles or doubles
        event_type = event[1].upper() if len(event) > 1 else None

        if event_type == "S":
            participants = player_count
        elif event_type == "D":
            participants = player_count // 2
            if player_count % 2 != 0:
                print(f"⚠️ Warning: Event {event} has an odd number of players ({player_count}), one will be left out.")
        else:
            print(f"⚠️ Warning: Event {event} has unknown type — skipping.")
            continue

        participants_structure[event] = participants

        # Compute number of matches per round
        rounds = []

        # If number of participants is 1, no matches
        if participants <= 1:
            elimination_structure[event] = []
            continue

        # Find the smallest power of 2 that is >= participants
        x = math.ceil(math.log2(participants))

        # Determine first round matches
        half = participants / 2
        if 2 ** x == half:
            first_round = int(2 ** x)
        else:
            first_round = int(participants - 2 ** (x - 1))

        rounds.append(first_round)

        # Subsequent rounds (each halving matches)
        matches = 2 ** (x - 2)
        while matches >= 1:
            rounds.append(matches)
            matches //= 2

        elimination_structure[event] = rounds

    return elimination_structure, participants_structure

def check_rule_violations(player_events):
    warnings = []

    for player, events in player_events.items():
        events = list(events)

        # Rule 1: If playing a V event, no other event with same prefix
        v_prefixes = {e[:2] for e in events if e.endswith("V")}
        for prefix in v_prefixes:
            conflicting = [e for e in events if e.startswith(prefix) and not e.endswith("V")]
            if conflicting:
                warnings.append(
                    f"⚠️ {player}: plays {', '.join([e for e in events if e.startswith(prefix) and e.endswith('V')])}, "
                    f"so cannot play {', '.join(conflicting)}"
                )

        # Rule 2: No more than 3 total events
        if len(events) > 3:
            warnings.append(f"⚠️ {player}: participates in {len(events)} events ({', '.join(events)})")

        # Rule 3: No more than two non-V events with same prefix
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

        # Rule 4: No 3+ events with second character D
        d_class_events = [e for e in events if len(e) > 1 and e[1].upper() == "D"]
        if len(d_class_events) >= 3:
            warnings.append(
                f"⚠️ {player}: plays {len(d_class_events)} doubles classes ({', '.join(d_class_events)})"
            )

    return warnings

def find_problematic_players(player_events, event_players, event_correlations):
    problematic_players = {}
    checked_pairs = set()  # to avoid duplicate collision reports
    
    # Condition 1: Players in 3+ events
    '''
    for player, events in player_events.items():
        if len(events) >= 3:
            problematic_players.setdefault(player, []).append(
                f"Plays in {len(events)} events: {', '.join(sorted(events))}"
            )
    '''

    # Condition 2: Sole collision cause
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

def write_event_analysis_to_excel(file_path, event_correlations, elimination_data, event_players, sheet_name="Event Analysis"):
    """
    Adds/updates a sheet showing event collisions and elimination round info.
    """
    
    max_rounds = 0
    for _, rounds in elimination_data.items():
        max_rounds = max(max_rounds, len(rounds))

    book = load_workbook(file_path)

    # Create sheet if missing
    if sheet_name not in book.sheetnames:
        sheet = book.create_sheet(sheet_name)
        headers = ["Event", "Collides With", "Player amount"] + [f"Round {i+1}" for i in range(max_rounds)]
        sheet.append(headers)

    sheet = book[sheet_name]

    # Clear only the data area (keep headers & formatting)
    for row in sheet.iter_rows(min_row=2, max_col= (3 + max_rounds)):
        for cell in row:
            cell.value = None

    # Write new data
    current_row = 2
    for event, collisions in event_correlations.items():
        # Fetch rounds info
        if event not in elimination_data or not (isinstance(elimination_data[event], list)):
            print("‼ ERROR ‼ : the rounds for the event could not be attained")
            break
        rounds = elimination_data[event]

        # Fetch player amount
        player_amount = len(event_players[event])

        # Event name
        sheet.cell(row=current_row, column=1).value = event

        # Collisions
        sheet.cell(row=current_row, column=2).value = ", ".join(
            [f"{other} ({count})" for other, count in collisions]
        )

        # Player amounts
        sheet.cell(row=current_row, column=3).value = player_amount

        # Rounds in separate cells
        for i, match_count in enumerate(rounds, start=4):
            sheet.cell(row=current_row, column=i).value = match_count

        current_row += 1
    
    book.save(file_path)

    print(f"✅ Added events to '{sheet_name}' sheet in {file_path}")

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

    file_path = "Entries HBC Premier Elite 2024.xlsx"  # <-- your Excel file
    event_codes = {"W", "M", "X"}
    event_correlations, event_players, player_events = parse_competition_excel(file_path, event_codes)
    strong_collision, weak_collision = analyze_collisions(event_correlations)
    elimination_data, participants_structure = calculate_elimination_rounds(event_players)
    day_one = half_hour_slots("2025-10-10 09:00", "2025-10-10 21:00")
    day_two = half_hour_slots("2025-10-10 09:00", "2025-10-10 17:30")

    # Matchslots can be made in a similar way as matches in the future if there is a varying amount of fields per timeslot.
    # for now assume constant amount of fields
    timeslots = day_one + day_two
    fields = 10
    matchslots = timeslots * fields
    last_of_day1 = day_one * fields

    # 2d list where index is class and element is list of matches (size = rounds)
    elimination_data_minizinc = [i[1] for i in elimination_data.items()]

    event_number_dict = {i[1]: i[0] for i in enumerate(elimination_data.keys())}
    event_to_number = lambda x: event_number_dict[x] + 1

    # collisions paired up
    strong_collision_minizinc = [item for i, (_, values) in enumerate(strong_collision.items())
        for v in values
        for item in (i + 1, event_to_number(v))]
    
    print(weak_collision)

    weak_collision_minizinc = [item for i, (_, values) in enumerate(weak_collision.items())
        for v in values
        for item in (i + 1, event_to_number(v[0]))]

    print(weak_collision_minizinc)

    matches_minizic = []
    class_index = []
    round_index = []

    count = 1
    for outer in elimination_data_minizinc:
        class_index.append(count)
        for inner in outer:
            round_index.append(count)
            for _ in range(0, inner):
                matches_minizic.append(count)
                count += 1
    
    if print_lists:
        print("TIMESLOTS:")
        print(timeslots, end='\n\n')
        print("ELIMINATION DATA:")
        print(elimination_data_minizinc, end='\n\n')
        print("CLASS INDEXES:")
        print(class_index, end='\n\n')
        print("ROUND INDEXES:")
        print(round_index, end='\n\n')
        print("MATCHES:")
        print(matches_minizic, end='\n\n')
        print(strong_collision_minizinc, end='\n\n')

    data = {
        "strong_collision": strong_collision_minizinc,
        "weak_collision": weak_collision_minizinc,
        "matches": matches_minizic,
        "class_index": class_index,
        "round_index": round_index,
        "timeslots": timeslots,
        "fields": fields,
        "matchslots": matchslots,
        "last_of_day1": last_of_day1,
        "file_path": file_path
    }

    return data

def main():
    file_path = "Entries HBC Premier Elite 2024.xlsx"  # <-- your Excel file
    event_codes = {"W", "M", "X"}
    event_correlations, event_players, player_events = parse_competition_excel(file_path, event_codes)
    strong_collision, weak_collision = analyze_collisions(event_correlations)
    elimination_data, participants_structure = calculate_elimination_rounds(event_players)
    rule_violations = check_rule_violations(player_events)
    problematic_players = find_problematic_players(player_events, event_players, event_correlations)
    #write_player_events_to_excel(file_path, player_events, problematic_players, sheet_name="Player Events")
    #write_event_analysis_to_excel(file_path, event_correlations, elimination_data, event_players, sheet_name="Event Analysis")
    #log_rule_violations_to_excel(file_path, rule_violations, sheet_name="Rule Violations")
    time_slots = half_hour_slots("2025-10-10 09:00", "2025-10-10 13:30")
    

    #print(str(time_slots))

    # Print all players for all events
    '''
    print("\n=== Event -> Players ===")
    for event, players in event_players.items():
        print(f"{event}: {sorted(players)}")
    '''
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
    
    print("\n=== Events colliding with same last character ===")
    for event, others in strong_collision.items():
        print(f"{event}: {others}")
    
    # Print weak collitions for an event (with wight)
    
    print("\n=== Events colliding with different last character (with counts) ===")
    for event, others in weak_collision.items():
        print(f"{event}: {others}")
    
    # Print mathces per elimination round per event
    
    print("\n=== Elimination rounds and matches per round ===")
    for event, rounds in elimination_data.items():
        print(f"{event}: {rounds}")
    
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
    minizinc_data()