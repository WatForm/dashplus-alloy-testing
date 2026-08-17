sig top1 {}
sig top2 {}

sig e1 extends top1 {}
sig e2 extends top2 {}

sig f1 extends e1 {}

sig sib1 extends top1 {}
sig sib2 extends top2 {}

sig g in top1 + e2 {}

run {}