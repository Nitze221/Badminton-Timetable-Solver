include "alldifferent.mzn";

int: nof_classes;
int: nof_rounds;
int: nof_matches;
int: nof_umpire_matches;
int: nof_matches_no_umpire;
int: timeslots;
int: fields;
int: matchslots;
int: nof_strong_collisions;
int: nof_weak_collisions;
int: last_of_day1;
int: nof_elit_rounds;

array[1..nof_classes] of int: class_index;
array[1..nof_rounds] of int: round_index;
array[1..nof_matches] of var 1..matchslots: matches;
set of int: umpire_matches;
array[1..nof_matches_no_umpire] of var 1..matchslots: matches_no_umpire;
array[1..nof_strong_collisions] of int: strong_collision;
array[1..nof_weak_collisions] of int: weak_collision;

%array[1..nof_matches] of var 1..timeslots: match_time;
%array[1..nof_matches] of var 1..fields: match_field;

% check if a match is in a class
function bool: in_class(int: match, int: class) = 
    (match >= class_index[class] /\ (class == nof_classes \/ match < class_index[class + 1]));

% check if a match is in a round
function bool: in_round(int: match, int: iround) = 
    (match >= round_index[iround] /\ (iround == nof_rounds \/ match < round_index[iround + 1]));

% Return the class of a match
array[1..nof_matches] of int: class_of_match = 
    [min([i | i in 1..nof_classes where in_class(j, i)]) | j in 1..nof_matches];

% Return the round of a match
array[1..nof_matches] of int: round_of_match = 
    [min([i | i in 1..nof_rounds where in_round(j, i)]) | j in 1..nof_matches];

% Returns all matches in a class
array[1..nof_classes] of set of int: matches_in_class =
    [ if c < nof_classes then
          class_index[c] .. class_index[c+1] - 1
      else
          class_index[c] .. nof_matches
      endif
      | c in 1..nof_classes
    ];

% Returns all matches in a round
array[1..nof_rounds] of set of int: matches_in_round =
    [ if r < nof_rounds then
          round_index[r] .. round_index[r+1] - 1
      else
          round_index[r] .. nof_matches
      endif
      | r in 1..nof_rounds
    ];

% Returns all matches in a round that are not umpire matches
array[1..nof_rounds] of set of int: matches_in_round_no_umpire =
    [ if r < nof_rounds then
          round_index[r] .. round_index[r+1] - 1
      else
          round_index[r] .. nof_matches
      endif
      | r in 1..nof_rounds
    ];

% TRUE if the match is a semifinal or final
function bool: is_semi_or_final(int: match, int: class) =
    if class < nof_classes then
        match >= class_index[class + 1] - 3 /\ match < class_index[class + 1]
    else
        match >= nof_matches - 2
    endif;

array[1..nof_matches] of var 1..timeslots: time_of_match =
    [ (matches[i] - 1) div fields + 1 | i in 1..nof_matches ];
% ???
array[1..nof_matches] of var 1..fields: field_of_match =
    [ (matches[i] - 1) mod fields + 1 | i in 1..nof_matches ];







% all matches have an available timeslot 1
%constraint forall(t in 1..timeslots)(
 %   alldifferent([ field_of_match[i] | i in 1..nof_matches where time_of_match[i] == t ])
%);

% all matches have an available timeslot 2
constraint alldifferent(matches);

% All rounds in all classes are played in order
% Aka. Within a class, a match in a round with a higher index must have a higher matchslot number
constraint forall (i, j in 1..nof_matches where i < j /\ class_of_match[i] == class_of_match[j]) (matches[i] < matches[j]);


% There can only be 5 umpire matches per timeslot
constraint
    forall(ts in 1..timeslots)(
        sum([ bool2int(time_of_match[um] == ts) | um in umpire_matches ]) <= 5
    );

% umpire matches must have atleast 1 timeslot inbetween, all umpire matches are either in same timeslot or have a gap of >= 1 timeslot between them
array[1..card(umpire_matches)] of int: ums = sort([ m | m in umpire_matches ]);

constraint forall(i, j in 1..(nof_umpire_matches) where i < j) (
    abs(time_of_match[ums[i]] - time_of_match[ums[j]]) != 1
);

%constraint forall(i in 1..(nof_umpire_matches - 1)) (
 %   abs((matches[ums[i]] - 1) div fields - (matches[ums[i+1]] - 1) div fields) != 1
%);


% consecutive rounds in a class must have atleast 1 timeslot inbetween
constraint 
    forall(c in 1..nof_classes, r in 1..nof_rounds - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        abs(min([ matches[i] | i in matches_in_round[r+1] ]) - max([ matches[i] | i in matches_in_round[r] ])) >= 2 * fields
    );


% matches must be played within 1 or 2 rounds
constraint 
    forall(c in 6..nof_classes, r in (nof_elit_rounds+1)..nof_rounds) (
        %abs(max([ matches[i] | i in matches_in_round[r] ]) - min([ matches[i] | i in matches_in_round[r] ])) < 2 * fields
        if card(matches_in_round[r]) > 4 then
            abs((max([ matches[i] | i in matches_in_round[r] ]) - 1) div fields - (min([ matches[i] | i in matches_in_round[r] ]) - 1) div fields) < 2
        else
            abs((max([ matches[i] | i in matches_in_round[r] ]) - 1) div fields - (min([ matches[i] | i in matches_in_round[r] ]) - 1) div fields) < 1
        endif
    );


% Rundor i kolliderande klasser som inte hör till samma nivå får inte spelas på samma tidsslot
constraint
    forall(i in 1..nof_strong_collisions where i mod 2 == 1) (
        forall(c1 in matches_in_class[strong_collision[i]],
               c2 in matches_in_class[strong_collision[i+1]]) (
            abs(time_of_match[c1] - time_of_match[c2]) >= 2
       )
    );


% weak collision
constraint
    forall(i in 1..nof_weak_collisions where i mod 2 == 1) (
        forall(c1 in matches_in_class[weak_collision[i]],
               c2 in matches_in_class[weak_collision[i+1]]) (
            abs(time_of_match[c1] - time_of_match[c2]) >= 1
       )
    );


% All semi-finals and finals on day 2
constraint 
    forall (i in 1..nof_matches where is_semi_or_final(i, class_of_match[i])) (
        matches[i] > last_of_day1
    );


% Block any round from beeing split between two days
constraint
    (forall(r in 1..nof_rounds)(
        forall(m in matches_in_round[r])(m <= last_of_day1)
    \/
        forall(m in matches_in_round[r])(m > last_of_day1)
    ));


