sig A {}

fun p[a : A]: A
{
	a
}

run {
	all a:A | p[a] = a
} for 4 A