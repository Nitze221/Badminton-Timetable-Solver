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
int: nof_junior_classes;

int: V_start;
int: V_end;
int: A_start;
int: A_end;
int: junior_start;
int: junior_end;

int: nof_V_rounds;
int: nof_A_rounds;
int: nof_junior_rounds;

int: V_rounds_start;
int: V_rounds_end;
int: A_rounds_start;
int: A_rounds_end;
int: junior_rounds_start;
int: junior_rounds_end;

int: nof_matches;
int: nof_V_matches;
int: nof_A_matches;
int: nof_junior_matches;
int: nof_matches_rest;

int: nof_single_V_classes;
int: single_V_start;
int: single_V_end;

int: nof_single_V_rounds;
int: single_V_rounds_start;
int: single_V_rounds_end;

int: nof_single_V_matches;
set of int: single_V_matches;

/*
int: timeslots_12_fields;
int: timeslots_8_fields;
int: timeslots_6_fields;

int: fields_1;
int: fields_2;
int: fields_3;

int: matchslots_1;
int: matchslots_2;
int: matchslots_3;
*/

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
set of int: junior_matches;
set of int: matches_rest;





set of int: Matches = 1..nof_matches; % same as set of int: all_matches; ?????                              ??????????????????????????
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
        (min_match_time_in_round[r + 1] - max_match_time_in_round[r]) >= 6
    );

% V (x = 90)
constraint 
    forall(c in V_start..V_end, r in V_rounds_start..V_rounds_end - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        (min_match_time_in_round[r + 1] - max_match_time_in_round[r]) >= 6
    );

% A (x = 90)
constraint 
    forall(c in A_start..A_end, r in A_rounds_start..A_rounds_end - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        (min_match_time_in_round[r + 1] - max_match_time_in_round[r]) >= 6
    );

% rest (x = 90)
constraint 
    forall(c in (junior_end+1)..(V_start-1), r in (junior_rounds_end+1)..(V_rounds_start-1) - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        (min_match_time_in_round[r + 1] - max_match_time_in_round[r]) >= 6
    );
constraint 
    forall(c in (A_end+1)..nof_classes, r in (A_rounds_end+1)..nof_rounds - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        (min_match_time_in_round[r + 1] - max_match_time_in_round[r]) >= 6
    );
% redundant constraint to help pruning
constraint 
    forall(c in (1)..nof_classes, r in (1)..nof_rounds - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        (min_match_time_in_round[r + 1] - max_match_time_in_round[r]) >= 0
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
        if card(matches_in_round[r]) > 4 then
            (max_match_time_in_round[r] - min_match_time_in_round[r]) < 3
        else
            (max_match_time_in_round[r] - min_match_time_in_round[r]) < 1
        endif
    );

constraint
    forall(r in umpire_rounds)(
        if card(matches_in_round[r]) > 4 then % this number must be <= umpire_chairs
            (max_match_time_in_round[r] - min_match_time_in_round[r]) < 4
        else
            (max_match_time_in_round[r] - min_match_time_in_round[r]) < 1
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

% strong collisions
constraint
    forall(i in 1..nof_strong_collisions where i mod 2 == 1) (
       collisionClass(strong_collision[i], strong_collision[i+1], 4)
    );
% weak collision
constraint
    forall(i in 1..nof_weak_collisions where i mod 2 == 1) (
        collisionClass(weak_collision[i], weak_collision[i+1], 3)
    );

% super weak collision
constraint
    forall(i in 1..nof_super_weak_collisions where i mod 2 == 1) (
        collisionClass(super_weak_collision[i], super_weak_collision[i+1], 2)
    );



% Semi-finals and finals on day 2 for V classes
%constraint
 %   forall(c in V_start..V_end
  %  )(
   %     forall(i in matches_in_class[c] where is_semi_or_final(i, c)) (
    %        time_of_match[i] > last_of_day1
     %   )
    %);
    


% switch constraint to domain narrowing
% Tighten domains of finals in elit classes to be strictly after last_of_day1



% Block any round from beeing split between two days

constraint
    forall(r in 1..nof_rounds) (
        max_match_time_in_round[r] <= last_of_day1
        xor
        min_match_time_in_round[r] > last_of_day1
    );

%constraint exists(m in 1..nof_matches)(
 %   time_of_match[m] == last_of_day0 + 1
%);



% In classes with <= 3 rounds: all matches within (rounds * 10) timeslots
constraint
    forall(c in Classes where 
        card({r | r in Rounds where class_of_match[round_index[r]] == c}) <= 3
    )(
        max_match_time_in_class[c] - min_match_time_in_class[c] + 1 <= 20 % nof_rounds_in_class[c] * 10
    );

% In classes with <= 3 rounds: all matches on the same day, using precomputed min/max
%constraint
 %   forall(c in 1..nof_classes where 
  %      card({r | r in 1..nof_rounds where class_of_match[round_index[r]] == c}) <= 3
   % )(
    %    (max_match_time_in_class[c] <= last_of_day1)
     %   xor
      %  (min_match_time_in_class[c] > last_of_day1)
    %);



% In classes with > 3 rounds: all matches within (rounds * 15) timeslots
constraint
    forall(c in Classes where 
        card({r | r in Rounds where class_of_match[round_index[r]] == c}) > 3
    )(
        max_match_time_in_class[c] - min_match_time_in_class[c] + 1 <= nof_rounds_in_class[c] * 15
    );


% Aikataulua laadittaessa kullekin ottelulle tulee varata keskimäärin vähintään 30 minuuttia.
% All adjecent timeslots can max have field amount of matches
%constraint
 %   forall(ts in 1..timeslots_12_fields - 1)(
  %      sum([ bool2int(time_of_match[m] == ts \/ time_of_match[m] == ts + 1)
   %         | m in 1..nof_matches ]) <= fields_1
    %);
%constraint
 %   forall(ts in (timeslots_12_fields+1)..(timeslots_12_fields+timeslots_8_fields) - 1)(
  %      sum([ bool2int(time_of_match[m] == ts \/ time_of_match[m] == ts + 1)
   %         | m in 1..nof_matches ]) <= fields_2
    %);
%constraint
 %   forall(ts in (timeslots_12_fields+timeslots_8_fields+1)..(timeslots_12_fields+timeslots_8_fields+timeslots_6_fields) - 1)(
  %      sum([ bool2int(time_of_match[m] == ts \/ time_of_match[m] == ts + 1)
   %         | m in 1..nof_matches ]) <= fields_3
    %);

/*
% --- Global Constants ---
int: total_max_fields = max([fields_1, fields_2, fields_3]);

Define durations for every match (2 slots = 30 minutes)
array[Matches] of int: match_durations = [2 | m in Matches];
array[Matches] of int: court_usage = [1 | m in Matches];

% --- Dummy Tasks to handle variable court availability ---
We create "Fixed matches" that occupy the courts you don't have.

1. Block out fields when we drop from 12 to 8
int: dummy_8_start = timeslots_12_fields + 1;
int: dummy_8_dur = timeslots_8_fields;
int: dummy_8_req = total_max_fields - fields_2; % e.g., 12 - 8 = 4 courts blocked

% 2. Block out fields when we drop from 8 to 6
int: dummy_6_start = timeslots_12_fields + timeslots_8_fields + 1;
int: dummy_6_dur = timeslots_6_fields;
int: dummy_6_req = total_max_fields - fields_3; % e.g., 12 - 6 = 6 courts blocked

constraint cumulative(
    [time_of_match[m] | m in Matches] ++ [dummy_8_start, dummy_6_start],
    match_durations ++ [dummy_8_dur, dummy_6_dur],
    court_usage ++ [dummy_8_req, dummy_6_req],
    total_max_fields
);

array[Matches] of int: durations = [2 | _ in Matches];  % Each match occupies 2 timeslots
array[Matches] of int: resources = [1 | _ in Matches];

constraint cumulative(time_of_match, durations, resources, fields_1);
*/

set of int: Blocks = 1..nof_blocks;

% --- Global Constants ---
int: total_max_fields = max(block_fields);
int: total_timeslots = sum(block_timeslots);

% Define durations for every match (2 slots = 30 minutes)
% Umpire matches take 3 slots (45 min), all other matches take 2 slots (30 min)
array[Matches] of int: match_durations = [
    if m in umpire_matches then 3 else 2 endif 
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

% 2 hours = 8 timeslots (the extra rest needed on top of the 12h night gap)
%int: night_buffer = 8;
%
%constraint
 %   forall(c in junior_start..junior_end) (
  %      let {
   %         set of int: m_in_c = matches_in_class[c]
    %    } in (
     %        % Gap between Day 0 and Day 1
      %      forall(m0 in m_in_c, m1 in m_in_c where 
       %         time_of_match[m0] <= last_of_day0 /\ 
        %        time_of_match[m1] > last_of_day0 /\ time_of_match[m1] <= last_of_day1
         %   ) (
                % The distance in slots across the boundary must be >= buffer
                % Because Day 1 starts immediately after last_of_day0 in the index,
                % we just need to ensure the slot difference is at least 8.
          %      time_of_match[m1] - time_of_match[m0] >= night_buffer
           % )
            %/\
            % Gap between Day 1 and Day 2
            %forall(m1 in m_in_c, m2 in m_in_c where 
             %   time_of_match[m1] > last_of_day0 /\ time_of_match[m1] <= last_of_day1 /\
              %  time_of_match[m2] > last_of_day1
            %) (
             %   time_of_match[m2] - time_of_match[m1] >= night_buffer
            %)
        %)
    %);
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
% solve minimize (max(time_of_match) - min(time_of_match)) 

%solve minimize 
 %   ((max(time_of_match) - min(time_of_match)) * 100) 
  %  + sum(c in 1..nof_classes)(max_match_time_in_class[c] - min_match_time_in_class[c]);

solve :: int_search(time_of_match, smallest, indomain_min)
    minimize 
        % Primary goal: Keep the whole day as short as possible
        ((max(time_of_match) - min(time_of_match)) * 100) 
        
        % Secondary goal: Tighten the rounds within each class
        + sum(c in 1..nof_classes)(max_match_time_in_class[c] - min_match_time_in_class[c]);





% Junnu - Ikäkausiluokissa 13, 11 ja 9 edellisen kilpailupäivän viimeisen ja seuraavan kilpailupäivän ensimmäisen pelin alkamisaikojen välin tulee olla vähintään 14 tuntia.












% hela Elit och A finaler ska ha domare

% Max 4 elit matcher på en gång


constraint
    cumulative(
        [time_of_match[um] | um in umpire_matches],
        [3 | um in umpire_matches],      % 3 x 15-minute slots
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

% Jos pelimuodossa on Valio- tai A-luokassa enemmän kuin 16 pelaajaa tai peliparia, kaikkia otteluita ei ilman SSuL:n kilpailutoimintaryhmän myöntämää poikkeuslupaa saa pelata samana päivänä ellei kilpailukutsussa mainita kilpailun olevan yksipäiväisen.
constraint
    forall(c in (V_start..V_end) union (A_start..A_end) where nof_rounds_in_class[c] > 4)(
        % The class cannot both start and end on Saturday
        not (max_match_time_in_class[c] <= last_of_day1)
        /\
        % The class cannot both start and end on Sunday
        not (min_match_time_in_class[c] > last_of_day1)
    );




    % Junnu - Kolmen tai neljän osanottajan poolin kaikkien otteluiden alkamisaikojen tulee olla viiden tunnin sisällä