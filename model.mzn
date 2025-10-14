int: n;
array[1..n] of int: values;
var int: total = sum(values);

solve satisfy;

output ["Total = \(total)\n"];
