sig A {}

pred p[a : A, b : A]
{
	some a
}

run {

univ.(none.p)

} for exactly 2 A