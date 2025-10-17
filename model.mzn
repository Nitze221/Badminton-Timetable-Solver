include "alldifferent.mzn";
include "at_most.mzn";
include "arg_max.mzn";
include "arg_min.mzn";
include "strictly_increasing.mzn";
include "disjunctive.mzn"

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
int: nof_super_weak_collisions;
int: last_of_day1;
int: nof_elit_rounds;
int: nof_elit_classes;

array[1..nof_classes] of int: class_index;
array[1..nof_rounds] of int: round_index;
array[1..nof_matches] of var 1..matchslots: matches;
set of int: umpire_matches;
array[1..nof_matches_no_umpire] of int: matches_no_umpire;
array[1..nof_strong_collisions] of int: strong_collision;
array[1..nof_weak_collisions] of int: weak_collision;
array[1..nof_super_weak_collisions] of int: super_weak_collision;

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


array[1..nof_rounds] of var int: max_match_index_in_round =
    [ matches_in_round[r][arg_max([ matches[i] | i in matches_in_round[r] ])]
      | r in 1..nof_rounds ];


array[1..nof_rounds] of var int: min_match_index_in_round =
    [ matches_in_round[r][arg_min([ matches[i] | i in matches_in_round[r] ])]
      | r in 1..nof_rounds ];





% all matches have an available timeslot
%constraint forall(t in 1..timeslots)(
 %   alldifferent([ field_of_match[i] | i in 1..nof_matches where time_of_match[i] == t ])
%);

% all matches have an available timeslot

constraint alldifferent(matches);

% All rounds in all classes are played in order
% Aka. Within a class, a match in a round with a higher index must have a higher matchslot number
% constraint forall (i, j in 1..nof_matches where i < j /\ class_of_match[i] == class_of_match[j]) (matches[i] < matches[j]);

constraint forall(c in 1..nof_classes)(
    strictly_increasing([matches[i] | i in matches_in_class[c]])
);

%constraint forall (c in 1..nof_classes) (
 %   forall (i in 1..(card(matches_in_class[c]) - 1)) (
  %      matches[i] < matches[i + 1]
   % )
%);

%constraint 
 %   forall(c in 1..nof_classes, r in 1..nof_rounds - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
  %      max([ matches[i] | i in matches_in_round[r] ]) <
   %     min([ matches[i] | i in matches_in_round[r+1] ])
    %);


% All rounds in a class must have atleast 2 timeslots inbetween them: slot_diff >= 20
% Also checks that matches in same round is within 2 timeslots (= denotes logical equivalence)
%constraint forall (i, j in 1..nof_matches where i < j /\ class_of_match[i] == class_of_match[j]) (
%       (round_of_match[i] != round_of_match[j]) = (abs(match_time[i] - match_time[j]) >= 2)
%    );

%constraint

% There can only be 4 umpire matches per timeslot
constraint
    forall(ts in 1..timeslots)(
        sum([ bool2int(time_of_match[um] == ts) | um in umpire_matches ]) <= 5
    );

% umpire matches must have atleast 1 timeslot inbetween, all umpire matches are either in same timeslot or have a gap of >= 1 timeslot between them
array[1..card(umpire_matches)] of int: ums = sort([ m | m in umpire_matches ]);

constraint forall(i, j in 1..(nof_umpire_matches) where i < j) (
    not (abs(time_of_match[ums[i]] - time_of_match[ums[j]]) in 1..2)
);

%constraint forall(i in 1..(nof_umpire_matches - 1)) (
 %   abs((matches[ums[i]] - 1) div fields - (matches[ums[i+1]] - 1) div fields) != 1
%);


% consecutive rounds in a class must have atleast 60 min inbetween
%constraint 
%    forall(c in 1..nof_classes, r in 1..nof_rounds - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
%        abs(min([ matches[i] | i in matches_in_round[r+1] ]) - max([ matches[i] | i in matches_in_round[r] ])) > 3 * fields
%
%    );

%constraint 
%    forall(c in 1..nof_classes, r in 1..nof_rounds - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
%        abs(time_of_match[min_match_index_in_round[r + 1]] - time_of_match[max_match_index_in_round[r]]) > 3
%    );

constraint 
    forall(c in 1..nof_classes, r in 1..nof_rounds - 1 where class_of_match[round_index[r]] == class_of_match[round_index[r + 1]]) (
        disjunctive(max_match_index_in_round[r], abs(time_of_match[min_match_index_in_round[r + 1]] - time_of_match[max_match_index_in_round[r]]) * 3)
    );


% matches must be played within 1 or 2 rounds
%constraint 
%    forall(c in (nof_elit_classes+1)..nof_classes, r in (nof_elit_rounds+1)..nof_rounds) (
%        %abs(max([ matches[i] | i in matches_in_round[r] ]) - min([ matches[i] | i in matches_in_round[r] ])) < 2 * fields
%        if card(matches_in_round[r]) > 4 then
%            abs((max([ matches[i] | i in matches_in_round[r] ]) - 1) div fields - (min([ matches[i] | i in matches_in_round[r] ]) - 1) div fields) < 3
%        else
%            abs((max([ matches[i] | i in matches_in_round[r] ]) - 1) div fields - (min([ matches[i] | i in matches_in_round[r] ]) - 1) div fields) < 2
%        endif
%    );

constraint
    forall(c in (nof_elit_classes+1)..nof_classes, r in (nof_elit_rounds+1)..nof_rounds)(
        if card(matches_in_round[r]) > 4 then
            abs(time_of_match[max_match_index_in_round[r]] - time_of_match[min_match_index_in_round[r]]) < 3
        else
            abs(time_of_match[max_match_index_in_round[r]] - time_of_match[min_match_index_in_round[r]]) < 2
        endif
    );


% strong collisions
constraint
    forall(i in 1..nof_strong_collisions where i mod 2 == 1) (
        forall(c1 in matches_in_class[strong_collision[i]],
               c2 in matches_in_class[strong_collision[i+1]]) (
            abs(time_of_match[c1] - time_of_match[c2]) >= 4
       )
    );


% weak collision
constraint
    forall(i in 1..nof_weak_collisions where i mod 2 == 1) (
        forall(c1 in matches_in_class[weak_collision[i]],
               c2 in matches_in_class[weak_collision[i+1]]) (
            abs(time_of_match[c1] - time_of_match[c2]) >= 3
       )
    );

% super weak collision
constraint
    forall(i in 1..nof_super_weak_collisions where i mod 2 == 1) (
        forall(c1 in matches_in_class[super_weak_collision[i]],
               c2 in matches_in_class[super_weak_collision[i+1]]) (
            abs(time_of_match[c1] - time_of_match[c2]) > 0
       )
    );


% All semi-finals and finals on day 2
%constraint 
 %   forall (i in 1..nof_matches where is_semi_or_final(i, class_of_match[i])) (
  %      matches[i] > last_of_day1
   % );

% Semi-finals and finals on day 2 only for classes with 5 or more rounds
constraint
    forall(c in 1..nof_classes where 
        card({r | r in 1..nof_rounds where class_of_match[round_index[r]] == c}) >= 5
    )(
        forall(i in matches_in_class[c] where is_semi_or_final(i, c)) (
            matches[i] > last_of_day1
        )
    );



% solve :: int_search(matches, first_fail, indomain_min, complete) satisfy;

% Block any round from beeing split between two days
constraint
    (forall(r in 1..nof_rounds)(
        forall(m in matches_in_round[r])(m <= last_of_day1)
    \/
        forall(m in matches_in_round[r])(m > last_of_day1)
    ));

constraint (min(matches) == 1);

% All adjecent timeslots can max have filed amount of matches
constraint
    forall(ts in 1..timeslots - 1)(
        sum([ bool2int(time_of_match[m] == ts \/ time_of_match[m] == ts + 1)
            | m in 1..nof_matches ]) <= fields
    );

% In classes with ≤ 3 rounds:
%  all matches must start within (rounds-of-class * 8) timeslots
%  all matches must also be on the same day (either all ≤ last_of_day1 or all > last_of_day1)
constraint
    forall(c in 1..nof_classes where 
        card({r | r in 1..nof_rounds where class_of_match[round_index[r]] == c}) <= 3
    )(
        let {
            set of int: mc = matches_in_class[c],
            var int: min_t = min([ time_of_match[m] | m in mc ]),
            var int: max_t = max([ time_of_match[m] | m in mc ]),
            int: nof_rounds_in_class = card({r | r in 1..nof_rounds where class_of_match[round_index[r]] == c})
        } in
            (max_t - min_t + 1 <= nof_rounds_in_class * 8)
    );

% In classes with <= 4 rounds
% All rounds should be played on the same day
constraint
    forall(c in 1..nof_classes where 
        card({r | r in 1..nof_rounds where class_of_match[round_index[r]] == c}) <= 4
    )(
        let {
            set of int: mc = matches_in_class[c],
            var int: min_t = min([ time_of_match[m] | m in mc ]),
            var int: max_t = max([ time_of_match[m] | m in mc ]),
            int: nof_rounds_in_class = card({r | r in 1..nof_rounds where class_of_match[round_index[r]] == c})
        } in
            (forall(m in mc)(matches[m] <= last_of_day1) \/ forall(m in mc)(matches[m] > last_of_day1))
    );

% In classes with > 3 rounds
%  all matches must start within (rounds-of-class * 10) timeslots
constraint
    forall(c in 1..nof_classes where 
        card({r | r in 1..nof_rounds where class_of_match[round_index[r]] == c}) > 3
    )(
        let {
            set of int: mc = matches_in_class[c],
            var int: min_t = min([ time_of_match[m] | m in mc ]),
            var int: max_t = max([ time_of_match[m] | m in mc ]),
            int: nof_rounds_in_class = card({r | r in 1..nof_rounds where class_of_match[round_index[r]] == c})
        } in
            (max_t - min_t + 1 <= nof_rounds_in_class * 10)
    );


solve minimize max(matches)