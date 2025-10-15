include "alldifferent.mzn";

int: nof_classes;
int: nof_rounds;
int: nof_matches;
int: timeslots;
int: fields;
int: matchslots;
int: nof_strong_collisions;
int: nof_weak_collisions;
int: last_of_day1;

array[1..nof_classes] of int: class_index;
array[1..nof_rounds] of int: round_index;
array[1..nof_matches] of var 1..matchslots: matches;
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

array[1..nof_classes] of set of int: matches_in_class =
    [ if c < nof_classes then
          class_index[c] .. class_index[c+1] - 1
      else
          class_index[c] .. nof_matches
      endif
      | c in 1..nof_classes
    ];

array[1..nof_rounds] of set of int: matches_in_round =
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

array[1..nof_matches] of var 1..fields: field_of_match =
    [ (matches[i] - 1) mod fields + 1 | i in 1..nof_matches ];


constraint forall(t in 1..timeslots)(
    alldifferent([ field_of_match[i] | i in 1..nof_matches where time_of_match[i] == t ])
);

% all matches have an available timeslot

% constraint alldifferent(matches);

% All rounds in all classes are played in order
% Aka. Within a class, a match in a round with a higher index must have a higher matchslot number
% constraint forall (i, j in 1..nof_matches where i < j /\ class_of_match[i] == class_of_match[j]) (matches[i] < matches[j]);

constraint 
    forall(c in 1..nof_classes, r in 1..nof_rounds - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        max([ matches[i] | i in matches_in_round[r] ]) <
        min([ matches[i] | i in matches_in_round[r+1] ])
    );


% All rounds in a class must have atleast 2 timeslots inbetween them: slot_diff >= 20
% Also checks that matches in same round is within 2 timeslots (= denotes logical equivalence)
%constraint forall (i, j in 1..nof_matches where i < j /\ class_of_match[i] == class_of_match[j]) (
%       (round_of_match[i] != round_of_match[j]) = (abs(match_time[i] - match_time[j]) >= 2)
%    );

%constraint
%  forall(i in 1..nof_classes,
%         j, k in matches_in_class[i] where j < k) (
%    (round_of_match[j] != round_of_match[k]) = (abs(((matches[j] - 1) div fields) - ((matches[k] - 1) div fields)) >= 2)
%  );

constraint 
    forall(c in 1..nof_classes, r in 1..nof_rounds - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        abs(max([ matches[i] | i in matches_in_round[r] ]) - min([ matches[i] | i in matches_in_round[r+1] ])) >= 2 * fields
    );

constraint 
    forall(c in 1..nof_classes, r in 1..nof_rounds - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        abs(max([ matches[i] | i in matches_in_round[r] ]) - min([ matches[i] | i in matches_in_round[r] ])) < 2 * fields
    );

% Rundor i kolliderande klasser som inte hör till samma nivå får inte spelas på samma tidsslot
%constraint
%    forall(i in 1..nof_strong_collisions where i mod 2 == 1) (
%        forall(c1 in matches_in_class(strong_collision[i]),
%               c2 in matches_in_class(strong_collision[i+1])) (
%            abs(((matches[c1] - 1) div fields) - ((matches[c2] - 1) div fields)) >= 1
%       )
%    );

% weak collision
%constraint
%    forall(i in 1..nof_weak_collisions where i mod 2 == 1) (
%        forall(c1 in matches_in_class(weak_collision[i]),
%               c2 in matches_in_class(weak_collision[i+1])) (
%            abs((matches[c1] div fields) - (matches[c2] div fields)) >= 1
%        )
%    );

% All semi-finals and finals on day 2
%constraint 
%    forall (i in 1..nof_matches where is_semi_or_final(i, class_of_match[i])) (
%        matches[i] > last_of_day1
%    );

% solve :: int_search(matches, first_fail, indomain_min, complete) satisfy;
