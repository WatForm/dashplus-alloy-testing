sig A {}

pred p[a : A, b : A]
{
	some b
}

run {

univ.(none.p)

} for exactly 2 A