sig B {}
sig A {
	f : B,
	g : B,
	h : B

}


run {
	f = none -> none
	some univ
	no univ

} for exactly 4 A, exactly 4 B