sig A {}
sig B {}

pred p[a: A, b: B]
{
	a = b
}

run {} for 4 A