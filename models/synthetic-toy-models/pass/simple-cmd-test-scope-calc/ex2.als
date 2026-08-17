sig A {}

sig A1, A2 extends A {}

run {} for 3 but exactly 2 A1, exactly 1 A2

run {} for 3 but exactly 2 A1, 1 A2

run {} for 1 but exactly 2 A1, 1 A2

run {} for 7 but exactly 2 A1, 1 A2
