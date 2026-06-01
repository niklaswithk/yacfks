# Mechanics
Taken from Daryl and frak, thir DC posts and frak's frakinator

Troops from leader and joiners are added togheter.
So each side gets 3 lines of combined inf, cav and archers.
base stats from mixing/combining tiers are calculated usnig a geometric weghted mean.
stat bonuses including widgets from rally lead are applied.
pets from rally lead(?) stack bonuses(?) additivley or multiplitavely (?). like bear trap level bouns(?)

the dmg fomrula is calclauted per line/troop type, using effective base stats and effective stats bonuses.
skills from heroes/troops stack the SkillMod damage multipler, which is also part of the dmg fomrula.
Troop skills are only applied per respective troop type of course, and some hero skills (gen4 and above) too.

So the dmg is differnet for each attack phase (i.e. inf damage, cav dmg, arch dmg) in any given turn.

targeting: first opposing infantry.
if opposing infantry is gone, oppoisng cav is next.
if oppoisiung cav is gone, opposing archers are next.

cav >=T7 gets a special RNG skill that has a hcance to re-target, whereby the cav can instead target enemy archers directly.


some hero skill are turn based, some attack based[attack-phase based], turn based applies for all 3 attacak phaes in a given turn.
attack-phase based rolls for each attack phase()

battles are turn based, for every turn there's 3(6) attack phases, one for each troop type/army line (and for each side, so 6 phases per turn)
AFTER all types/army lines and both sides have had a go at each other, casualites are removed from the equiation, so no side gets an advatange DURING a turn.
so kills/casulaites are removed from the battle sim at the end of a turn.
and the next turn thus starts with both sides having taking casualites, and the dmg fomrula is applied again according to the above.

when a turn starts, stat and troops are calculated in this order:

* Attackers effects are applied
* attackers chance-based effects are rolled and applied/procs if roll sucess
* Attackers damage fomrula is applied
* Defenders effects are applied
* Defenders chance-based effects are rolled and applied/procs if roll sucess
* Defenders damage fomrula is applied
* Attackers kills calcualted
* defenders kills calculated
* Turn ends
* then the next turn begins with the remaining troops on both sides until one side runs out of troops.

"effects" here must refer to skills from heroes & troops. some skills are just simply static and always present for every turn(as long as that hero/hero skil/troop/troop skill is present)
some skills are RNG.
And as stated above, a clarification about RNG skills - some roll once per turn, in the beginning.
while some roll for every attack phase (probably, lets assume this for now)