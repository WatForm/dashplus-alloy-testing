sig A {}

fun p[a : A]
{
	a
}

run {
	p[a] = a
} for 4 A