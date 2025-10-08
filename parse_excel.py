import pandas as pd
from collections import defaultdict, Counter
import math

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



if __name__ == "__main__":
    file_path = "./2025/Premier Elite/Entries HBC Premier Elite 2024.xlsx"  # <-- your Excel file
    event_codes = {"W", "M", "X"}
    event_correlations, event_players, player_events = parse_competition_excel(file_path, event_codes)
    strong_collision, weak_collision = analyze_collisions(event_correlations)
    elimination_data, participants_structure = calculate_elimination_rounds(event_players)
    warnings = check_rule_violations(player_events)


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
    print("\n=== Elimination rounds and matches per round ===")
    for event, rounds in elimination_data.items():
        print(f"{event}: {rounds}")
    '''
    # Print warnings related to players entries
    '''
    for warning in warnings:
        print(warning)
    '''
