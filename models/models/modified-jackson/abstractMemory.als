// module chapter6/memory/abstractMemory [Addr, Data] ----- the model from page 217

sig Memory {
	data: Addr -> lone Data
	}

pred init [m: Memory] {
	no m.data
	}

pred write [m, m_prime: Memory, a: Addr, d: Data] {
	m_prime.data = m.data ++ a -> d
	}

pred read [m: Memory, a: Addr, d: Data] {
	let d_prime = m.data [a] | some d_prime implies d = d_prime
	}

fact Canonicalize {
	no disj m, m_prime: Memory | m.data = m_prime.data
	}

// This command should not find any counterexample
WriteRead: check {
	all m, m_prime: Memory, a: Addr, d1, d2: Data |
		write [m, m_prime, a, d1] and read [m_prime, a, d2] => d1 = d2
	}

// This command should not find any counterexample
WriteIdempotent: check {
	all m, m_prime, m": Memory, a: Addr, d: Data |
		write [m, m_prime, a, d] and write [m_prime, m", a, d] => m_prime = m"
	}
