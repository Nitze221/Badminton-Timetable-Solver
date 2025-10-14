include "alldifferent.mzn";

int: nof_classes;
int: nof_rounds;
int: nof_matches;
int: timeslots;
int: fields;
int: matchslots;
int: nof_strong_collisions;

array[1..nof_classes] of int: class_index;
array[1..nof_rounds] of int: round_index;
array[1..nof_matches] of var int: matches;
array[1..nof_strong_collisions] of int: strong_collision;

% check if a match is in a class
function bool: in_class(int: match, int: class) = 
    (match >= class_index[class] /\ (class == nof_classes \/ match < class_index[class + 1]));

% check if a match is in a round
function bool: in_round(int: match, int: iround) = 
    (match >= round_index[iround] /\ (iround == nof_rounds \/ match < round_index[iround + 1]));

% Return the class of a match
function int: class_of(int: match) =
    min([i | i in 1..nof_classes where in_class(match, i)]);

% Return the round of a match
function int: round_of(int: match) =
    min([i | i in 1..nof_rounds where in_round(match, i)]);

function set of int: matches_in_class(int: c) =
    if c < nof_classes then
        class_index[c] .. class_index[c+1] - 1
    else
        class_index[c] .. nof_matches
    endif;

% all matches have an available timeslot
constraint forall (i in 1..nof_matches) (matches[i] >= 1 /\ matches[i] <= matchslots);

% All rounds in all classes are played in order
% Aka. Within a class, a match in a round with a higher index must have a higher matchslot number
constraint forall (i, j in 1..nof_matches where i < j /\ class_of(i) == class_of(j)) (matches[i] < matches[j]);

% All rounds in a class must have atleast 2 timeslots inbetween them: slot_diff >= 20
% Also checks that matches in same round is within 2 timeslots (= denotes logical equivalence)
constraint forall (i, j in 1..nof_matches where i < j /\ class_of(i) == class_of(j)) (
        (round_of(i) != round_of(j)) = (abs(matches[i] - matches[j]) >= 2 * fields)
    );
% No matches at the same time on the same field
constraint alldifferent(matches);

% Rundor i kolliderande klasser som inte hör till samma nivå får inte spelas på samma tidsslot
constraint
    forall(i in 1..nof_strong_collisions where i mod 2 == 1) (
        forall(c1 in matches_in_class(strong_collision[i]),
               c2 in matches_in_class(strong_collision[i+1])) (
            if round_of(c1) == round_of(c2) then
                abs(matches[c1] - matches[c2]) >= fields
            else
                true
            endif
        )
    );