sig A {}

fun choose[first, second: A]: A {
    first
}

fact {
    #A = 2
    all x, y: A | y.(x.choose) = x
}

run {} for 2