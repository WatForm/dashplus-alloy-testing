sig A {}
sig B {}

sig A1, A2 extends A {}

one sig A1one extends A1 {}

sig A11, A12 extends A1 {}


run {} for 3 but exactly 2 A11

run {} for 1 but exactly 2 A11

run {} for 7 but exactly 2 A11

run {} for 7 but exactly 2 A11, 4 A2

run {} for 3 but exactly 2 A11, 4 A2

run {} for 3 but exactly 2 A11, exactly 4 A2

run {} for 3 but exactly 2 A11, exactly 4 A2, exactly 5 A12

run {} for 3 but exactly 2 A11, exactly 5 A12

run {} for 3 but exactly 2 A11, exactly 5 A12, 4 A1

run {} for 3 but exactly 2 A11, exactly 5 A12, exactly 4 A1