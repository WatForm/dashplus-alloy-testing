sig A {}

fun choose[first, second: A]: A {
    first
}

fact {
    #A = 2
    all x, y: A | choose[x][y] = x
}

run {} for 2