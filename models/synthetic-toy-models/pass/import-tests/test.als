open util/ordering[A1]
open util/ordering[A2] as A2
open util/ordering[A3]
open mymod[A4]
open util/ordering[A3]


sig A {}

sig A1,A2,A3,A4 extends A {}

run {} for exactly 3 A1,  4 A, 5 B, 4 C

