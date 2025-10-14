include "alldifferent.mzn";

int: nof_classes;
int: nof_rounds;
int: nof_matches;
int: timeslots;
int: fields;
int: matchslots;

array[1..nof_classes] of int: class_index;
array[1..nof_rounds] of int: round_index;
array[1..nof_matches] of var int: matches;

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

% all matches have an available timeslot
constraint forall (i in 1..nof_matches) (matches[i] >= 1 /\ matches[i] <= matchslots);

% All rounds in all classes are played in order
% Aka. Within a class, a match in a round with a higher index must have a higher matchslot number
constraint forall (i, j in 1..nof_matches where i < j /\ class_of(i) == class_of(j)) (matches[i] < matches[j]);

% All rounds in a class must have atleast 2 timeslots inbetween them: slot_diff >= 20
constraint forall (i, j in 1..nof_matches where i < j /\ round_of(i) != round_of(j) /\ class_of(i) == class_of(j)) (
        abs(matches[i] - matches[j]) >= 2*fields
    );
% No matches at the same time on the same field
constraint alldifferent(matches);

solve satisfy;
