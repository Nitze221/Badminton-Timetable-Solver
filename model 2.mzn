include "alldifferent.mzn";
% model_fixed.mzn - timetable solver (cleaned and extended with round constraints)

int: nof_classes;
int: nof_rounds;

int: nof_matches;                % matches that may require an umpire
int: nof_matches_no_umpire;      % matches without umpire
int: nof_umpire_matches;
int: timeslots;                  % number of start times (15 min each)
int: fields;                      % number of fields (matches that may start at same timeslot)
int: matchslots;                 % total slot id count = timeslots * fields

int: nof_strong_collisions;
int: nof_weak_collisions;
int: last_of_day1;
int: nof_elit_rounds;

array[1..nof_classes] of int: class_index; % start match index for each class (1-based)
array[1..nof_rounds]  of int: round_index; % start match index for each round (1-based)
%array[1..nof_rounds]  of int: round_class; % which class each round belongs to (1..nof_classes)

array[1..nof_matches] of var 1..matchslots: matches;
set of int: umpire_matches; % subset of 1..nof_matches identifying umpire matches
array[1..nof_matches_no_umpire] of var 1..matchslots: matches_no_umpire;

% collisions are flattened pairs of CLASS ids:
array[1..nof_strong_collisions] of int: strong_collision;
array[1..nof_weak_collisions] of int: weak_collision;

% ---------------- Derived ----------------
int: tot_matches = nof_matches;

array[1..tot_matches] of var 1..matchslots: all_matches =
    [ if i <= nof_matches then matches[i] else matches_no_umpire[i - nof_matches] endif
      | i in 1..tot_matches ];

function var int: slot_to_timeslot(var int: s) = ((s - 1) div fields) + 1;
function var int: slot_to_field(var int: s)    = ((s - 1) mod fields) + 1;

array[1..tot_matches] of var 1..timeslots: start_ts;
array[1..tot_matches] of var 1..fields:   the_field;

constraint
  forall(i in 1..tot_matches) (
    start_ts[i] = slot_to_timeslot(all_matches[i]) /\
    the_field[i] = slot_to_field(all_matches[i])
  );

% durations: umpire -> 3 timeslots (45 min), others -> 2 timeslots (30 min)
array[1..tot_matches] of int: duration =
    [ if idx <= nof_matches then
         (if idx in umpire_matches then 3 else 2 endif)
      else
         2
      endif
      | idx in 1..tot_matches ];

% distinct start slots
constraint all_different(all_matches);

% don't overflow end of day
constraint forall(i in 1..tot_matches) (
  start_ts[i] + duration[i] - 1 <= timeslots
);

% no overlapping matches on same field
constraint
  forall(i, j in 1..tot_matches where i < j) (
    if the_field[i] = the_field[j] then
      (start_ts[i] + duration[i] - 1 < start_ts[j]) \/
      (start_ts[j] + duration[j] - 1 < start_ts[i])
    else
      true
    endif
  );

% ==========================
% CLASS & ROUND HELPERS
% ==========================

function bool: in_class(int: match, int: class) =
    match >= class_index[class] /\ (class == nof_classes \/ match < class_index[class + 1]);

function bool: in_round(int: match, int: iround) =
    match >= round_index[iround] /\ (iround == nof_rounds \/ match < round_index[iround + 1]);

% Returns all matches in a class (covers tot_matches now)
array[1..nof_classes] of set of int: matches_in_class =
    [ if c < nof_classes then
          class_index[c] .. class_index[c+1] - 1
      else
          class_index[c] .. tot_matches
      endif
      | c in 1..nof_classes
    ];

% Returns all matches in a round (covers tot_matches now)
array[1..nof_rounds] of set of int: matches_in_round =
    [ if r < nof_rounds then
          round_index[r] .. round_index[r+1] - 1
      else
          round_index[r] .. tot_matches
      endif
      | r in 1..nof_rounds
    ];

% =========================
% STRONG & WEAK COLLISIONS
% =========================

int: STRONG_GAP = 4; % 1 hour = 4 * 15min slots
int: WEAK_GAP   = 3; % 45 min = 3 * 15min slots

% --- Strong collisions ---
%constraint
%  assert(nof_strong_collisions mod 2 = 0,
%         "strong_collision array length must be even") /\
%  forall(k in 1..(nof_strong_collisions div 2)) (
%    let {
%      int: c1 = strong_collision[2*k-1],
%      int: c2 = strong_collision[2*k]
%    } in
%    c1 >= 1 /\ c1 <= nof_classes /\
%    c2 >= 1 /\ c2 <= nof_classes /\
%    forall(m1 in matches_in_class[c1], m2 in matches_in_class[c2]) (
%      abs(start_ts[m1] - start_ts[m2]) >= STRONG_GAP
%    )
%  );

% --- Weak collisions ---
%constraint
%  assert(nof_weak_collisions mod 2 = 0,
%         "weak_collision array length must be even") /\
%  forall(k in 1..(nof_weak_collisions div 2)) (
%    let {
%      int: c1 = weak_collision[2*k-1],
%      int: c2 = weak_collision[2*k]
%    } in
%    c1 >= 1 /\ c1 <= nof_classes /\
%    c2 >= 1 /\ c2 <= nof_classes /\
%    forall(m1 in matches_in_class[c1], m2 in matches_in_class[c2]) (
%      abs(start_ts[m1] - start_ts[m2]) >= WEAK_GAP
%    )
%  );

% ==========================
% ROUND CONSTRAINTS
% ==========================

% 1) All matches in same round must have start times within 45 minutes
constraint
  forall(r in 1..nof_rounds) (
    forall(m1, m2 in matches_in_round[r]) (
      abs(start_ts[m1] - start_ts[m2]) <= WEAK_GAP
    )
  );

% 2) Rounds in the same class must be separated by at least 60 minutes
%    We assume round_index order corresponds to round order; if round ordering
%    is not guaranteed, adjust accordingly.
%constraint
%  forall(r1, r2 in 1..nof_rounds where r1 < r2 /\ round_class[r1] = round_class[r2]) (
%    forall(m1 in matches_in_round[r1], m2 in matches_in_round[r2]) (
%      start_ts[m2] - start_ts[m1] >= STRONG_GAP
%    )
%  );

%solve satisfy;

output [
  "Total matches scheduled: ", show(tot_matches), "\n",
  "Format per line: match_index | slot_id | timeslot | field | duration | covers_timeslots\n",
  concat([ show(i) ++ " | " ++ show(all_matches[i]) ++ " | " ++ show(start_ts[i]) ++ " | " ++ show(the_field[i])
           ++ " | " ++ show(duration[i]) ++ " | " ++ show(start_ts[i]) ++ "-" ++ show(start_ts[i] + duration[i] - 1) ++ "\n"
           | i in 1..tot_matches ])
];
