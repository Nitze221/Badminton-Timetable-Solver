
import competition_info
import parse_excel

def write_into_to_excel():
    print("\n\n----Running parse_excel.py----\n")
    
    file_path = competition_info.file_path
    #file_path = "Entries Dubbelturnering 2026 1.1. .xlsx"#"Junnu entries.xlsx"  # <-- your Excel file
    print(f"Reading from and writing to '{file_path}'\n")
    print("Performed action:")
    event_correlations, event_players, player_events = parse_excel.parse_competition_excel(file_path)
    if not event_correlations and not event_players and not player_events:
        print("❌ ERROR: No data was loaded from the excel (file name likely wrong). QUITTING!")
        print("\n----Done due to error----\n")
        return
    event_structures, round_schedules = parse_excel.calculate_tournament_structure(event_players, competition_info.pool)
    rule_violations = parse_excel.check_rule_violations(player_events)
    problematic_players = parse_excel.find_problematic_players(player_events, event_players, event_correlations)
    event_colors = parse_excel.assign_event_colors(event_players.keys(), parse_excel.color_bank)
    parse_excel.write_player_events_to_excel(file_path, player_events, problematic_players, sheet_name="Player Events")
    parse_excel.write_event_analysis_to_excel(file_path, event_correlations, round_schedules, event_structures, event_colors, event_players, sheet_name="Event Analysis")
    parse_excel.log_rule_violations_to_excel(file_path, rule_violations, sheet_name="Rule Violations")
    
    print("\n----Done----\n")