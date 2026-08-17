/* 
    A -> 3
    A1 -> exactly 2
*/

sig A {}
sig A1 extends A {}

run {} for 4 but exactly 2 A1, 5 int

run {} for exactly 2 A1, 6 Int, 1 A

run {} for exactly 2 A1, exactly 7 A

run {} for exactly 2 A1, exactly 1 A

run {} for exactly 2 A1, exactly 2 A

run {} for exactly 2 A1, 2 A