include "alldifferent.mzn";
include "global_cardinality.mzn";
include "increasing.mzn";
include "strictly_increasing.mzn";
include "cumulative.mzn";

int: umpire_chairs;

int: nof_strong_collisions;
int: nof_weak_collisions;
int: nof_super_weak_collisions;

int: nof_classes;
int: nof_rounds;

int: nof_V_classes;
int: nof_A_classes;
int: nof_B_classes;
int: nof_C_classes;
int: nof_junior_classes;
int: nof_rest_classes;

int: V_start;
int: V_end;
int: A_start;
int: A_end;
int: B_start;
int: B_end;
int: C_start;
int: C_end;
int: junior_start;
int: junior_end;
int: rest_start;
int: rest_end;

int: nof_V_rounds;
int: nof_A_rounds;
int: nof_B_rounds;
int: nof_C_rounds;
int: nof_junior_rounds;
int: nof_rest_rounds;

int: V_rounds_start;
int: V_rounds_end;
int: A_rounds_start;
int: A_rounds_end;
int: B_rounds_start;
int: B_rounds_end;
int: C_rounds_start;
int: C_rounds_end;
int: junior_rounds_start;
int: junior_rounds_end;
int: rest_rounds_start;
int: rest_rounds_end;

int: nof_matches;
int: nof_V_matches;
int: nof_A_matches;
int: nof_B_matches;
int: nof_C_matches;
int: nof_junior_matches;
int: nof_matches_rest;

int: nof_singles_classes;
int: nof_doubles_classes;
int: nof_singles_rounds;
int: nof_doubles_rounds;
int: nof_singles_matches;
int: nof_doubles_matches;

int: nof_single_V_classes;
int: single_V_start;
int: single_V_end;

int: nof_single_V_rounds;
int: single_V_rounds_start;
int: single_V_rounds_end;

int: nof_single_V_matches;
set of int: single_V_matches;

int: nof_blocks;
array[Blocks] of int: block_starts;
array[Blocks] of int: block_timeslots;
array[Blocks] of int: block_fields;
array[Blocks] of int: block_matchslots;

int: last_of_day1;
int: last_of_day0;

set of int: all_matches;
set of int: V_matches;
set of int: A_matches;
set of int: B_matches;
set of int: C_matches;
set of int: junior_matches;
set of int: matches_rest;

set of int: V_classes;
set of int: A_classes;
set of int: B_classes;
set of int: C_classes;
set of int: junior_classes;
set of int: rest_classes;

set of int: V_rounds;
set of int: A_rounds;
set of int: B_rounds;
set of int: C_rounds;
set of int: junior_rounds;
set of int: rest_rounds;

set of int: singles_classes;
set of int: doubles_classes;
set of int: singles_rounds;
set of int: doubles_rounds;
set of int: singles_matches;
set of int: doubles_matches;

int: strong_collisions;
int: weak_collisions;
int: super_weak_collisions;
    
int: V_round_gap;
int: A_round_gap;
int: rest_round_gap;
int: junior_round_gap;
    
int: deciding_U_round_factor;
int: U_big_round_start_duration;
int: U_small_round_start_duration;
    
int: deciding_rest_round_factor;
int: big_round_start_duration;
int: small_round_start_duration;

int: U_match_duration;
int: rest_match_duration;
    
int: deciding_class_factor;
int: big_class_duration;
int: small_class_duration;

int: max_round_gap;





set of int: Matches = 1..nof_matches; % same as set of int: all_matches; ?????                               ??????????????????????????
%set of int: Slots = 1..(timeslots_12_fields+timeslots_8_fields+timeslots_6_fields);
set of int: Slots = 1..total_timeslots;
% set of int: Fields_1 = 1..fields;
% set of int: Fields_2 =
% set of int: Fields_3 = 
%set of int: Fields = 1..fields;

set of int: Classes = 1..nof_classes;
set of int: Rounds = 1..nof_rounds;

array[Classes] of Matches: class_index;
array[Rounds] of Matches: round_index;

set of int: umpire_matches = 
    { m | c in V_start..V_end, m in matches_in_class[c] } union
    { m | c in A_start..A_end, m in matches_in_class[c] where is_final(m, c) };

set of int: matches_no_umpire =
    Matches diff umpire_matches;

% A round is an umpire round if at least one of its matches requires an umpire
set of int: umpire_rounds = {
    r | r in Rounds where card(matches_in_round[r] intersect umpire_matches) > 0
};

set of int: no_umpire_rounds = Rounds diff umpire_rounds;

array[1..nof_strong_collisions] of Classes: strong_collision;
array[1..nof_weak_collisions] of Classes: weak_collision;
array[1..nof_super_weak_collisions] of Classes: super_weak_collision;

array[Matches] of var Slots: time_of_match;

array[Matches] of Slots: warm_values;

% check if a match is in a class
function bool: in_class(int: match, int: class) = 
    (match >= class_index[class] /\ (class == nof_classes \/ match < class_index[class + 1]));

% check if a match is in a round
function bool: in_round(int: match, int: iround) = 
    (match >= round_index[iround] /\ (iround == nof_rounds \/ match < round_index[iround + 1]));

% Return the class of a match
array[Matches] of Classes: class_of_match = 
    [min([i | i in Classes where in_class(j, i)]) | j in Matches];

% Return the round of a match
array[Matches] of Rounds: round_of_match = 
    [min([i | i in Rounds where in_round(j, i)]) | j in Matches];

% Returns all matches in a class
array[Classes] of set of Matches: matches_in_class =
    [ if c < nof_classes then
          class_index[c] .. class_index[c+1] - 1
      else
          class_index[c] .. nof_matches
      endif
      | c in Classes
    ];

% Returns all rounds in a class
array[Classes] of set of Rounds: rounds_in_class =
    [ if c < nof_classes then
          round_of_match[class_index[c]] .. round_of_match[class_index[c + 1]] - 1
      else
          round_of_match[class_index[c]] .. nof_rounds
      endif
      | c in Classes
    ];

% Returns number of rounds in a class
array[Classes] of Rounds: nof_rounds_in_class =
    [ length(rounds_in_class[c])
      | c in Classes
    ];

% Returns all matches in a round
array[Rounds] of set of Matches: matches_in_round =
    [ if r < nof_rounds then
          round_index[r] .. round_index[r+1] - 1
      else
          round_index[r] .. nof_matches
      endif
      | r in Rounds
    ];


% Returns all matches in a round that are not umpire matches
%array[1..nof_rounds] of set of int: matches_in_round_no_umpire =
 %   [ if r < nof_rounds then
  %        round_index[r] .. round_index[r+1] - 1
   %   else
    %      round_index[r] .. nof_matches
     % endif
      %| r in 1..nof_rounds
    %];

% TRUE if the match is a round of 16, quarterfinal, semifinal or final (last 15 matches of the class)
function bool: is_r16_quarter_semi_or_final(int: match, int: class) =
    let {
        int: c_start = class_index[class];
        int: c_end   = if class < nof_classes then class_index[class + 1] - 1 else nof_matches endif;
        int: r16_start = max(c_start, c_end - 14);
    } in (
        match >= r16_start /\ match <= c_end
    );

% TRUE if the match is a quarterfinal, semifinal or final (last 7 matches of the class)
function bool: is_quarter_semi_or_final(int: match, int: class) =
    let {
        int: c_start = class_index[class];
        int: c_end   = if class < nof_classes then class_index[class + 1] - 1 else nof_matches endif;
        int: qf_start = max(c_start, c_end - 6);
    } in (
        match >= qf_start /\ match <= c_end
    );

% TRUE if the match is a semifinal or final (last 3 matches of the class)
function bool: is_semi_or_final(int: match, int: class) =
    let {
        int: c_start = class_index[class];
        int: c_end   = if class < nof_classes then class_index[class + 1] - 1 else nof_matches endif;
        int: sf_start = max(c_start, c_end - 2);
    } in (
        match >= sf_start /\ match <= c_end
    );

% TRUE if the match is a final (last match of the class)
function bool: is_final(int: match, int: class) =
    let {
        int: c_end = if class < nof_classes then class_index[class + 1] - 1 else nof_matches endif;
    } in (
        match == c_end
    );
%array[Matches] of var 1..timeslots: time_of_match =
%    [ (matches[i] - 1) div fields + 1 | i in Matches ];
% ???
%array[Matches] of var 1..fields: field_of_match =
%    [ (matches[i] - 1) mod fields + 1 | i in Matches ];


array[Rounds] of var Slots: max_match_time_in_round =
    [ if r < nof_rounds then
          time_of_match[round_index[r+1] - 1]
      else
          time_of_match[nof_matches]
      endif
      | r in Rounds
    ];


array[Rounds] of var Slots: min_match_time_in_round =
    [ time_of_match[round_index[r]] | r in Rounds ];

array[Classes] of var Slots: max_match_time_in_class =
    [ if c < nof_classes then
          time_of_match[class_index[c+1] - 1]
      else
          time_of_match[nof_matches]
      endif
      | c in Classes
    ];


array[Classes] of var Slots: min_match_time_in_class =
    [ time_of_match[class_index[c]] | c in Classes ];






% --- Within each round: matches are non-decreasing (optional) ---
constraint
    forall(r in Rounds)(
        increasing([time_of_match[m] | m in matches_in_round[r]])
    );

constraint
    forall(c in Classes)(
        increasing([time_of_match[m] | m in matches_in_class[c]])
        /\
        strictly_increasing([max_match_time_in_round[r] | r in rounds_in_class[c]])
        /\
        strictly_increasing([min_match_time_in_round[r] | r in rounds_in_class[c]])
    );

% --- Between consecutive rounds in the same class: strict increase ---
%constraint
%    forall(c in Classes, r in 1..nof_rounds-1 where
%        class_of_match[round_index[r]] == c /\ class_of_match[round_index[r+1]] == c
%    )(
%        max_match_time_in_round[r] < min_match_time_in_round[r+1]
%    );

% anchor
%constraint
%    forall(r in Rounds)(
%        time_of_match[min(matches_in_round[r])] = min_match_time_in_round[r]
%    );

% tighten domains
constraint forall(r in Rounds, i in matches_in_round[r]) (
    %min_match_time_in_round[r] <= time_of_match[i] /\
    time_of_match[i] <= max_match_time_in_round[r]
);



% This HAS to be better, right?
%constraint
 %   cumulative(
  %      [time_of_match[um] | um in umpire_matches],
   %     [3 | um in umpire_matches],       % each umpire match spans 3 consecutive slots (gap)
    %    [1 | um in umpire_matches],       % each uses 1 unit of resource capacity
     %   5                                 % at most 5 umpire matches simultaneously (chairs)
    %);



% consecutive rounds in a class must have atleast x min inbetween

% junior (x = 75)
constraint 
    forall(c in junior_start..junior_end, r in junior_rounds_start..junior_rounds_end - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        (min_match_time_in_round[r + 1] - max_match_time_in_round[r]) >= junior_round_gap
    );

% V (x = 90)
constraint 
    forall(c in V_start..V_end, r in V_rounds_start..V_rounds_end - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        (min_match_time_in_round[r + 1] - max_match_time_in_round[r]) >= V_round_gap
    );

% A (x = 90)
constraint 
    forall(c in A_start..A_end, r in A_rounds_start..A_rounds_end - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        (min_match_time_in_round[r + 1] - max_match_time_in_round[r]) >= A_round_gap
    );

% rest (x = 90)
constraint 
    forall(c in (junior_end+1)..(V_start-1), r in (junior_rounds_end+1)..(V_rounds_start-1) - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        (min_match_time_in_round[r + 1] - max_match_time_in_round[r]) >= rest_round_gap
    );
%????????????????????
constraint 
    forall(c in (A_end+1)..nof_classes, r in (A_rounds_end+1)..nof_rounds - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        (min_match_time_in_round[r + 1] - max_match_time_in_round[r]) >= rest_round_gap
    );
% redundant constraint to help pruning
constraint 
    forall(c in (1)..nof_classes, r in (1)..nof_rounds - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        (min_match_time_in_round[r + 1] - max_match_time_in_round[r]) >= 0
    );

% MAX time between rounds 4 * 6 = 24 = 6 hours
constraint 
    forall(c in Classes, r in 1..nof_rounds - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        (min_match_time_in_round[r + 1] - max_match_time_in_round[r]) < max_round_gap
    );

%constraint
%    forall(c in (nof_elit_classes+1)..nof_classes)(
%        disjunctive(
%            [min_match_time_in_round[r] | r in rounds_in_class[c] intersect (nof_elit_rounds+1)..nof_rounds],
%            [max_match_time_in_round[r] - min_match_time_in_round[r] + 4 | r in rounds_in_class[c] intersect (nof_elit_rounds+1)..nof_rounds]
%        )
%    );

% elite not needed, we want more strict rule, which holds for all umpire matches, not just consecutive rounds
%constraint 
%    forall(c in 1..nof_elit_classes, r in 1..nof_elit_rounds - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
%        (min_match_time_in_round[r + 1] - max_match_time_in_round[r]) >= 4
%    );
%constraint 
%    forall(c in Classes, r in Rounds - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
%        disjunctive(max_match_index_in_round[r], abs(time_of_match[min_match_index_in_round[r + 1]] - time_of_match[max_match_index_in_round[r]]) * 3)
%    );


% matches must be played within 1 or 2 rounds

constraint
    forall(r in no_umpire_rounds)(
        if card(matches_in_round[r]) > deciding_rest_round_factor then
            (max_match_time_in_round[r] - min_match_time_in_round[r]) < big_round_start_duration
        else
            (max_match_time_in_round[r] - min_match_time_in_round[r]) < small_round_start_duration
        endif
    );

constraint
    forall(r in umpire_rounds)(
        if card(matches_in_round[r]) > deciding_U_round_factor then % this number must be <= umpire_chairs
            (max_match_time_in_round[r] - min_match_time_in_round[r]) < U_big_round_start_duration
        else
            (max_match_time_in_round[r] - min_match_time_in_round[r]) < U_small_round_start_duration
        endif
    );

%constraint
 %   forall(r in 1..nof_elit_rounds)(
  %      if card(matches_in_round[r]) > 4 then
   %         (max_match_time_in_round[r] - min_match_time_in_round[r]) < (((card(matches_in_round[r]) - 1) div 5) + 1) * 3
    %    else
     %       (max_match_time_in_round[r] - min_match_time_in_round[r]) < 2
      %  endif
    %);



% collisions only between max(min(c1), min(c2)) and min(max(c1), max(c2))

predicate collision(int: r1, int: r2, int: gap) =
    ((max_match_time_in_round[r1] + gap <= min_match_time_in_round[r2])
    xor
    (max_match_time_in_round[r2] + gap <= min_match_time_in_round[r1]));

predicate noOverlap(int: r1, int: r2) =
    ((max_match_time_in_round[r1] + 0 <= min_match_time_in_round[r2])
    xor
    (max_match_time_in_round[r2] + 0 <= min_match_time_in_round[r1]));

predicate collisionClass(int: c1, int: c2, int: gap) =
    forall(r1 in rounds_in_class[c1],
            r2 in rounds_in_class[c2]) (
            collision(r1, r2, gap)
       );

predicate collisionClassFrontier(int: c1, int: c2, int: gap) =
    let {
        array[int] of Rounds: r1 = [r | r in rounds_in_class[c1]],
        array[int] of Rounds: r2 = [r | r in rounds_in_class[c2]],
        int: n1 = length(r1),
        int: n2 = length(r2),
        
        % Exactly n1 integer variables instead of (n1 * n2) booleans!
        array[1..n1] of var 1..n2 + 1: first_after
    } in
    % 1. Monotonicity along A: an earlier round of A finishes earlier, 
    % so its first_after index in B must be <= that of later rounds
    forall(i in 1..n1 - 1)(
        first_after[i] <= first_after[i + 1]
    )
    /\
    % 2. Forward disjunction: All rounds of B from first_after[i] onward must start after A[i]
    forall(i in 1..n1, j in 1..n2)(
        (j >= first_after[i]) -> (max_match_time_in_round[r1[i]] + gap <= min_match_time_in_round[r2[j]])
    )
    /\
    % 3. Backward disjunction: All rounds of B before first_after[i] must finish before A[i]
    forall(i in 1..n1, j in 1..n2)(
        (j < first_after[i]) -> (max_match_time_in_round[r2[j]] + gap <= min_match_time_in_round[r1[i]])
    );

predicate collisionClassFrontierPerDay(int: c1, int: c2, int: gap) =
    let {
        array[int] of Rounds: r1 = [r | r in rounds_in_class[c1]],
        array[int] of Rounds: r2 = [r | r in rounds_in_class[c2]],
        int: n1 = length(r1),
        int: n2 = length(r2),
        
        % Exactly n1 integer variables instead of (n1 * n2) booleans!
        array[1..n1] of var 1..n2 + 1: first_after
    } in
    % 1. Monotonicity along A
    forall(i in 1..n1 - 1)(
        first_after[i] <= first_after[i + 1]
    )
    /\
    % 2. Forward disjunction: Enforce gap only if on the same day
    forall(i in 1..n1, j in 1..n2)(
        (j >= first_after[i] /\ day_of_round[r1[i]] == day_of_round[r2[j]]) 
        -> (max_match_time_in_round[r1[i]] + gap <= min_match_time_in_round[r2[j]])
    )
    /\
    % 3. Backward disjunction: Enforce gap only if on the same day
    forall(i in 1..n1, j in 1..n2)(
        (j < first_after[i] /\ day_of_round[r1[i]] == day_of_round[r2[j]]) 
        -> (max_match_time_in_round[r2[j]] + gap <= min_match_time_in_round[r1[i]])
    );

% strong collisions
constraint
    forall(i in 1..nof_strong_collisions where i mod 2 == 1) (
       collisionClassFrontierPerDay(strong_collision[i], strong_collision[i+1], strong_collisions)
    );
% weak collision
constraint
    forall(i in 1..nof_weak_collisions where i mod 2 == 1) (
        collisionClassFrontierPerDay(weak_collision[i], weak_collision[i+1], weak_collisions)
    );

% super weak collision
constraint
    forall(i in 1..nof_super_weak_collisions where i mod 2 == 1) (
        collisionClassFrontierPerDay(super_weak_collision[i], super_weak_collision[i+1], super_weak_collisions)
    );

% Block any round from beeing split between two days
% 1 = Day 1 / Saturday, 2 = Day 2 / Sunday
set of int: DayIndices = 1..2;
array[Rounds] of var DayIndices: day_of_round;

constraint forall(r in Rounds)(
    % Day 1:
    (day_of_round[r] == 1 <-> max_match_time_in_round[r] <= last_of_day1)
    /\
    % Day 2:
    (day_of_round[r] == 2 <-> min_match_time_in_round[r] > last_of_day1)
);


% In classes with <= 3 rounds: all matches within (rounds * 10) timeslots
constraint
    forall(c in Classes where 
        card({r | r in Rounds where class_of_match[round_index[r]] == c}) <= deciding_class_factor
    )(
        max_match_time_in_class[c] - min_match_time_in_class[c] + 1 <= small_class_duration % nof_rounds_in_class[c] * 10
    );


% In classes with > 3 rounds: all matches within (rounds * x) timeslots
constraint
    forall(c in Classes where 
        card({r | r in Rounds where class_of_match[round_index[r]] == c}) > deciding_class_factor
    )(
        max_match_time_in_class[c] - min_match_time_in_class[c] + 1 <= nof_rounds_in_class[c] * big_class_duration
    );

set of int: Blocks = 1..nof_blocks;

% --- Global Constants ---
int: total_max_fields = max(block_fields);
int: total_timeslots = sum(block_timeslots);

% Define durations for every match (2 slots = 30 minutes)
% Umpire matches take 3 slots (45 min), all other matches take 2 slots (30 min)
array[Matches] of int: match_durations = [
    if m in umpire_matches then U_match_duration else rest_match_duration endif 
    | m in Matches
];
array[Matches] of int: court_usage = [1 | m in Matches];

% --- Dynamic Dummy Tasks to handle variable court availability ---
% We create a "Fixed task" for each block that occupies (total_max_fields - block_fields[b]) courts.
array[Blocks] of int: dummy_starts = block_starts;
array[Blocks] of int: dummy_durs   = block_timeslots;
array[Blocks] of int: dummy_reqs   = [total_max_fields - block_fields[b] | b in Blocks];

constraint cumulative(
    [time_of_match[m] | m in Matches] ++ dummy_starts,
    match_durations ++ dummy_durs,
    court_usage ++ dummy_reqs,
    total_max_fields
);


/*
% --- Lunch Break Configuration ---
int: lunch_start_slot = 9;  % 11:00
int: lunch_end_slot = 23;   % 14:30
int: lunch_gap = 8;         % 2 hours = 8 * 15min

constraint
    forall(c in 1..nof_classes)(
        let {
            % Get the list of rounds belonging to this specific class
            array[int] of int: c_rounds = [r | r in 1..nof_rounds where class_of_match[round_index[r]] == c]
        } in 
        forall(i in 1..length(c_rounds)-1)(
            let {
                int: r_current = c_rounds[i],
                int: r_next = c_rounds[i+1]
            } in
            % CHECK: Is this the FIRST round of the class to start in the lunch window?
            if (min_match_time_in_round[r_current] >= lunch_start_slot /\ 
                min_match_time_in_round[r_current] <= lunch_end_slot /\
                % Either it's the first round of the class, or the round before it started before 11:00
                (i == 1 \/ min_match_time_in_round[c_rounds[i-1]] < lunch_start_slot))
            then
                % Apply the 2-hour gap only once
                min_match_time_in_round[r_next] >= min_match_time_in_round[r_current] + lunch_gap
            else 
                true 
            endif
        )
    );
*/

var int: makespan =
    max(time_of_match);

var int: morning_gravity =
    sum(r in Rounds, m in matches_in_round[r])(
        time_of_match[m] - if day_of_round[r] == 2 then last_of_day1 + 1 else 0 endif
    );

var int: class_span =
    sum(c in 1..nof_classes)(max_match_time_in_class[c] - min_match_time_in_class[c]);

solve 
    minimize
        (makespan * 1000) + singles_doubles_overlap_penalty;

/*
solve :: warm_start(time_of_match, warm_values)
    minimize 
        % Primary goal: Keep the whole day as short as possible
        class_span * pow(10,6)
        +
        morning_gravity;

constraint makespan == 83;
*/


% Junnu - Ikäkausiluokissa 13, 11 ja 9 edellisen kilpailupäivän viimeisen ja seuraavan kilpailupäivän ensimmäisen pelin alkamisaikojen välin tulee olla vähintään 14 tuntia.












% hela Elit och A finaler ska ha domare

% Max 4 elit matcher på en gång


constraint
    cumulative(
        [time_of_match[um] | um in umpire_matches],
        [U_match_duration | um in umpire_matches],      % 3 x 15-minute slots
        [1 | um in umpire_matches],      % Each match uses 1 chair
        umpire_chairs                    % Available umpire chairs
    );

% Elit finaler (och seminfinaler om det går) ska spelas på söndag (sista tävlingsdagen)

constraint
    let {
        set of int: v_finals = { m | c in V_start..V_end, m in matches_in_class[c] where is_semi_or_final(m, c) };
    } in (
        forall(m in v_finals) (
            time_of_match[m] > last_of_day1
        )
    );


% Valioluokan kaksinpelissä neljännesvälierä-, puolivälierä-, välierä- ja loppuotteluiden alkamisaikojen välillä tulee olla vähintään 3 tuntia (12 * 15 min = 180 min)
constraint
    forall(c in single_V_start..single_V_end, r in single_V_rounds_start..single_V_rounds_end - 1 
           where class_of_match[round_index[r]] == c /\ class_of_match[round_index[r + 1]] == c) (
        if is_r16_quarter_semi_or_final(round_index[r], c) then
            (min_match_time_in_round[r + 1] - max_match_time_in_round[r]) >= 12
        else
            true
        endif
    );

% Jos pelimuodossa on Valio- tai A-luokassa enemmän kuin 16 pelaajaa tai peliparia, 
% kaikkia otteluita ei ilman SSuL:n kilpailutoimintaryhmän myöntämää poikkeuslupaa 
% saa pelata samana päivänä ellei kilpailukutsussa mainita kilpailun olevan yksipäiväisen.
constraint
    forall(c in (V_start..V_end) union (A_start..A_end) where nof_rounds_in_class[c] > 4)(
        % The class cannot both start and end on Saturday
        not (max_match_time_in_class[c] <= last_of_day1)
        /\
        % The class cannot both start and end on Sunday
        not (min_match_time_in_class[c] > last_of_day1)
    );




    % Junnu - Kolmen tai neljän osanottajan poolin kaikkien otteluiden alkamisaikojen tulee olla viiden tunnin sisällä



% Annan optimering forutom makespan:

/*
1. För varje nivå (C, B, A, V, etc.)
    - första rundan av single spelas före första rundan av dubbel och mixed
    - sista rundan av singel spelas före sista rundan av dubbel och mixed (finaler)
    - Minimera overlap per dag

DET IDEALA (enlight Jori från kouvola):
1. För varje dag
    För varje nivå
    - all singel före all dubbel och mixed
*/

% -----------------------------------------------------------------------------
% SINGLES VS DOUBLES/MIXED ORDERING
% 1. Första rundan av singel spelas före första rundan av dubbel och mixed
% 2. Sista rundan av singel spelas före sista rundan av dubbel och mixed
% -----------------------------------------------------------------------------


% 1:
predicate order_first_and_last_rounds(set of int: level_classes) =
    let {
        set of int: lvl_singles = level_classes intersect singles_classes;
        set of int: lvl_doubles = level_classes intersect doubles_classes;
    } in 
    forall(c_s in lvl_singles, c_d in lvl_doubles) (
        % 1. First round of singles before first round of doubles
        (max_match_time_in_round[min(rounds_in_class[c_s])] < 
         min_match_time_in_round[min(rounds_in_class[c_d])])
        /\
        % 2. Last round (finals) of singles before last round (finals) of doubles
        (max_match_time_in_round[max(rounds_in_class[c_s])] < 
         min_match_time_in_round[max(rounds_in_class[c_d])])
    );

% Apply the constraint to each specific level
constraint order_first_and_last_rounds(V_classes);
constraint order_first_and_last_rounds(A_classes);
constraint order_first_and_last_rounds(B_classes);
constraint order_first_and_last_rounds(C_classes);
% constraint order_first_and_last_rounds(junior_classes);

% --- Soft constraint: Minimize overlap between singles and doubles per day ---
function var int: overlap_penalty(set of int: level_classes) =
    let {
        set of int: lvl_singles = level_classes intersect singles_classes;
        set of int: lvl_doubles = level_classes intersect doubles_classes;
    } in
    sum(
        c_s in lvl_singles,
        c_d in lvl_doubles,
        r_s in rounds_in_class[c_s],
        r_d in rounds_in_class[c_d]
        where day_of_round[r_s] == day_of_round[r_d]
    )(
        % Penalty grows the later singles finishes compared to the doubles start time
        max(0, max_match_time_in_round[r_s] - min_match_time_in_round[r_d])
    );

var int: singles_doubles_overlap_penalty = 
    overlap_penalty(V_classes) + 
    overlap_penalty(A_classes) + 
    overlap_penalty(B_classes) + 
    overlap_penalty(C_classes) + 
    overlap_penalty(junior_classes);