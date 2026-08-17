sig A {}
sig AA extends A {}
sig AAA extends AA {}
sig AAAA extends AAA {}

sig B extends AAAA {}
sig BB extends B {}
sig BBB extends BB {}
sig BBBB extends BBB {}

sig C extends BBBB {}
sig CC extends C {}
sig CCC extends CC {}
sig CCCC extends CCC {}

sig D extends CCCC {}
sig DD extends D {}
sig DDD extends DD {}
sig DDDD extends DDD {}


sig W extends DDDD {}
sig WW extends W {}
sig WWW extends WW {}
sig WWWW extends WWW {}

sig X extends WWWW {}
sig XX extends X {}
sig XXX extends XX {}
sig XXXX extends XXX {}

sig Y extends XXXX {}
sig YY extends Y {}
sig YYY extends YY {}
sig YYYY extends YYY {}

sig Z extends YYYY {}
sig ZZ extends Z {}
sig ZZZ extends ZZ {}
sig ZZZZ extends ZZZ {}

check {}