# yacfks Skills & Battle Engine Reference

## Core philosophy or "I got drunk and thought of something clever maybe"

Dwelling on hero/troop skills properties and how `SkillMod` is populated I've been trying to organize skills into a sort of unifying framework/model, where skills are made up of common building blocks like trigger type, conditions, effects, delay, duration etc.  
Many skills (perhaps all if Im lucky) could be defined using these building blocks. Many skills are simple enough to be anyway.  
If most/all skills can be defined with generalized building blocks, a battle/skills engine should be able to parse/evaluate skills components and stack the `SkillMod` on either side correclty with the skill effects & values. That would mean no ad-hoc handlers or custom code per hero/hero skill.  
It would also make skills composable, so one can try declaring a skill with certain properties and see how it turns out in simulations and if it  comes close to matching in-game battle reports. if not, one can change the skill and try again.

With yacfks i've tried implemetning this model, and a skills engine that apply effects from skills by parsing skill effect objects - skills become pure data, not code, and the skills engine evaluates and applies skill effects according to their definitions.

## in short
Hero & troop skills are defined as a trigger + conditions + one or more **`EffectSpec`** objects. `EffectSpec` holds `effect_type` & `effect_op`, benefactor/target scope (i.e. troop types involved), duration, delay, stack rule etc.

(I think the SoS simulator uses similar line of thinking with benefactor scopes and maybe more things like i do here, but im not sure as i havent' familiarized myslef with the SoS sim source)

A skill, when/if it fires (trigger types + conditions like RNG etc dictates when, or if, during a turn it can/will trigger), then each `EffectSpec` on the skill becomes an **`ActiveEffect`** stored in a list on the **skill host/skill caller side** within a `BattleState` object, where we can keep track of effects state/lifetime etc.  
The effect lives there across turns and is parsed on every relevant attack phase for the rest of its lifetime (governed by `duration`, `apply_delay`, `stack_rule`).
Eventually these effects are collected, or rather routed, into an EffectCollection object, which is capable of do SKillMod stacking of effect_type and effect_op according to damage formula.  
A skillmod numeartor is 1 EC, denomionator another EC.

A troop skill is based off of the same base class as hero skills, so they can too be created with duration, delay, benefactor/target scopes, conditions etc.  

A troop skill just needs to be present, e.g. we just need 1 T7 inf present in order to collect the troop skill Bands of Steel.  
As one user on DC put it when demonstrating this, "troop tiers are aggregated into one bucket per troop type, and any and all troop type skills are stickers slapped on that bucket"

Cav skill Ambusher is special, it is evalualted during the targeting setup at start of turn.  
Archer skill Volley will be special handled too, once implemented.

THe battle engine drives the turn loop, and within each turn we have attack phases, where troops on both sides exchange damage.  
Both Attacker and Defender becomes `phase attacker` and `phase defender` during a turn.  
Currently, for every turn, Attacker goes first with its attack phases (i.e. becomes "phase attacker"), one per troop type present.  
Then it's the Defender's turn to become "phase attacker", with its troop types dealing damage against Attacker, now being the phase defender.  
Then we reach the end of turn and casualties are calcuated after both sides have exchanged damage.

During the battle, at various points (start of the battle, start of every turn and most importantly for every attack phase, where a certain troop type on one side will deal damage against a certain troop type on the other side) the skills engine is invoked with a triggering type to eval, and using a `PhaseContext` (containing the intial battle setup/`BattleContext` and current `BattleState`) supplied by the battle engine, the skills engine has everything needed for the it to evaluate and promote skill effects to "Active" (or pending, if it has delay) by appedning a list of `ActiveEffects` within `BattleState`, thereby mutating the battle state.  
Both sides gets their own seperate lists for active and pending effects within `BattleState`.

THe trigger type dictates when during the battle/turn it will be evaluated by skills engine, while conditions (like RNG/must roll true, FriendlyTroopTypesRequired etc) governs wheter the skill evaluation will contionue or break/return.

Eventaully all active effects are used to compute an effect skillmod numerator and denominator.  
The skills engine routes an effect and its value into the skillmod numerator/denominator by way of effect_type, fetching "numerator" effect_types from phase attacker list of `ActiveEffects` and "denominator" effect_types from phase defender list of `ActiveEffects`.

More details below.

## Some terminology.

Battles are turn based, we all know that, and within any given turn both Attacker and Defender exchnge damage, so it's symetrical.  
the role of "Attacker"/"Defender" is mosstly releveant only for bonus resolving at start of battle/battle setup, i.e. stats bonuses from effective widget skills, which depends on what side you're on.  
So in a turn both sides sees their troop types deal and recieve damage from the other side, and the targeting alg should be familiar to everyone already.  

For clarity i differentiate bewteen "TURNS" and "PHASES":  
`TURN`: a battle turn, plain and simple. Within a turn, both Attacker and Defender will become both PHASE ATTACKER and PHASE DEFENDER before the turn is over.  

`PHASE`: an attack phase where one troop type on side deals damage against a troop type on the other side, e.g. INF vs INF or CAV vs ARCH.

`PHASE ATTACKER`: which side, Attacker or Defender, during a given turn whose troops are currently doing the attaking. for example when Defender troops deals damage against Attacker INF - Defender is currently `PHASE ATTACKER`. And `SELF_*` scopes would scope to Defender in this case.

`PHASE_DEFENDER`: Whichever side during a given turn whose troops are currently the ones recieving damage from PHASE_ATTACKER.

---

## Architecture Overview

```
Battle engine fires trigger event
  ↓
SkillEngine.evaluate_skills(hero_skills, troop_skills, trigger, context)
  ├─ For each hero skill: _apply_skill(definition, level, ...)
  │    → check trigger + conditions + level data
  │    → for each EffectSpec: _apply_effect → writes ActiveEffect to "skill host" side in BattleState
  │         apply_delay=0 → host_side active effects   (effective this turn)
  │         apply_delay>0 → host_side pending effects  (effective in a future turn)
  │
  └─ For each troop skill: _apply_skill(definition, level=1, ...)
       → essentially same path as hero skills — writes ActiveEffect to owner/skill host side in BattleState

Per attack phase:
  SkillEngine.build_phase_ecs(att_active_effects, def_active_effects, att_troop_type, target_troop_type)
    → att_active_effects: current phase attacker's active effects → NUMERATOR types read here
    → def_active_effects: current phase defender's active effects → DENOMINATOR types read here
    → returns (numerator_ec, denominator_ec)
  SkillEngine.compute_skill_mod(numerator_ec, denominator_ec)
    → returns SkillMod float → battle engine feeds into compute_kills()

Special troop skills (TROOP_SPECIAL trigger — Ambusher, future Volley):
  SkillEngine.collect_retarget(cav_troop_skills, context)
    → called once per turn before the attack phases start; returns True if RETARGET skill rolls true
    → BattleEngine switches CAV's target to ARCH if alive
```

---

## Data Models

### BattleState

`BattleState` holds current info about battle as it progresses.  
Active and pending effects are stored per side/particiapnt(Attacker & Defender).  
Each side hosts its own effects coming from their heroes, whether self buffs or enemy debuffs.  
The skills engine iterates both sides' lists of effects and by way of `effect_type` routes/places them into the correct sides Skillmod and numerator/denominator effects (see more under Routing rules below)

```python
BattleState:
    attacker_active_effects:  list[ActiveEffect]   # Attacker skill effects currently active & contributing
    attacker_pending_effects: list[ActiveEffect]   # Attacker pedning skill effects, i.e. skills/effects with a dealy, promoted in a futre turn
    defender_active_effects:  list[ActiveEffect]
    defender_pending_effects: list[ActiveEffect]

    def get_effects(self, side: BattleSide, *, pending: bool = False) -> list[ActiveEffect]:
        # returns the right list for the given side and active/pending flag
```

`_tick_statuses` runs at end of each turn and decrements `remaining_turns` (from an effects' `duration`) on active effects (removing those that reach 0), then promotes `pending_effects → active_effects` according to `apply_delay`.

### EffectSpec

Skill effect definition. An effect being that which you see in a skill description.  
EffectSpec is the atomic unit of a skill. Layering the model like this means effects are decoupled from skills, and a skill has 1 or more effects. Or more like buffs/debuffs placed somewhere in the battle.
Both hero and troop skills use this, and the effects when placed appends a list of `ActiveEffect`s in `BattleState`.

```python
EffectSpec:
    effect_type:      EffectType          # DAMAGE_UP | DEFENSE_UP | TROOP_DAMAGE_UP | TROOP_DEFENSE_UP
                                          # OPP_DEFENSE_DOWN | OPP_DAMAGE_DOWN
                                          # RETARGET (CAV speical skill) | EXTRA_ATK_PHASE (future Volley arch special skill)
    effect_op:        int                 # 101, 102, 201 etc etc
    target_scope:     TargetScope         # for filtering, resolves to target_troop; controls which phase the effect fires in
    benefactor_scope: TargetScope | None  # for filtering, restricts which own troop type benefits; None = all
    duration:         int = -1            # turns active; -1 = permanent
    apply_delay:      int = 0             # 0 = active this turn; N = active after N turns
    stack_rule:       StackRule = STACK   # STACK | UNIQUE | REFRESH
```

`target_scope` evenutally resvoles to a concrete TroopType in `ActiveEffect` (it does not control which side stores the effect — effects are always stored on the owner's side aka the skill host), where it's used a filter to determine during which attack phase the effect will apply.
This extra handling of `target_scope` is because an `EffectSpec` is frozen after it's instantiated while targeting can be dynamic with e.g. `CURRENT_TARGET`, so if one defines an effect with dynamic targeting it needs to resolve somewhere to an actual `TroopType`, and `ActiveEffect` is used for tracking such statefulness so that's where the resolved targeting  resides.

`benefactor_scope` serves a similar purpose as a filter, but currently it can stay in `EffectSpec`.  

`None` defaults to all i.e. any/all troop type vs any/all troop type.


### SkillLevelData

Numeric values for a skill at a specific level.

```python
SkillLevelData:
    skill_id: int
    level:    int
    values:   dict[int, float]   # effect_op → percentage value (e.g. {102: 25.0} = op 102 is +25%)
    chance:   float | None = None  # for skills where levels increase trigger chance. Overrides RandomChanceCondition.chance when set
```

### ActiveEffect

A live effect instance tracked in `BattleState`. One `ActiveEffect` per `EffectSpec` — each independently carries its placement, remaining lifetime, resolved numeric value from the skill level, and other contexts like resolved target `TroopType`.

```python
ActiveEffect:
    effect_spec:     EffectSpec          # The effect defintion, see `EffectSpec` above
    remaining_turns: int                 # -1 = permanent
    source_skill_id: int                 # which HeroSkillDefinition placed this
    host_side:       BattleSide          # the side (Attacker/Defender) hosting this effect
    target_troop:    TroopType | None    # resolved from target_scope in EffectSpec; None = any troop
    value:           float               # resolved from level_data at apply-time
```

`target_troop` is the concrete `TroopType` value resolved from `EffectSpec.target_scope`, see EffectSpec above. That's so that eg `CURRENT_TARGET` in `EffectSpec` will resolve to an acutal `TroopType` when tracked as an `ActiveEffect` in `BattelState`.  
Everything else about the effect can be accessed via `ActiveEffect.effect_spec`.

### SkillDefinition

Base class for `HeroSkillDefinition` and `TroopSkillDefinition`

### HeroSkillDefinition

Defines when a hero skill fires, under what conditions, and what effects it places.

```python
HeroSkillDefinition:
    id:         int
    name:       str
    trigger:    TriggerType
    effects:    list[EffectSpec]
    conditions: list[SkillCondition]
    level_data: dict[int, SkillLevelData] | None
```

### TroopSkillDefinition

Structurally identical to `HeroSkillDefinition`, both share the `SkillDefinition` base class with the same fields.  
Troop skills will prob be hardcoded, and regular non-RNG non-special troop skills will probably be defined with `TURN_START` trigger and `duration=1` or `STATIC` trigger and `duration=-1`, depends a bit on how they're gonna be counted once skill trigger/activation counting is implemented.

```python
TroopSkillDefinition:
    id:         int
    name:       str
    trigger:    TriggerType
    effects:    list[EffectSpec]
    conditions: list[SkillCondition]
    level_data: dict[int, SkillLevelData] | None
```

**Deduplication** for troop skills happens at army composition time. `ArmyLine.troop_skills` is a property that collects skills from all `TroopStack`s in the `ArmyLine` and dedupes by `skill.id`. So with e.g. T6 INF and T10 INF both will carry the troop skill "Master Brawler" (same `id`), and the army line exposes only one instance. The skill engine never sees duplicates.

---

## Trigger Types

Evaluation timing, ie when during a turn that a skill effect can/will be evaluated and possibly have it's effect, or effects, applied.

| Trigger          | When it "fires"                                    | Comment |
|---|---|---|
| `STATIC`         | Only once per battle, before the turn loop starts     |  |
| `TURN_START`     | Once per turn                    |  |
| `PHASE`          | Once per attack phase (per troop type) | E.g. Petras Evil Eye/"TknUp" skills, unless it's `TURN_START_PER_TROOP` |
| `TURN_START_PER_TROOP` | Like `PHASE` but fired at turn start and evals for every troop type present| E.g. Petras Evil Eye/"TknUp" skills unless regular `PHASE` |
| `TROOP_SPECIAL`  | Evaluated once at targeting resolving before attack phases start | AMBUSHER and VOLLEY |
| `EVERY_N_TURNS`  | **[Planned]** Once per turn when `turn % N == 0` — first fires on turn N, not turn 1 |  |

`PHASE` fires 6 times per turn total — 3 phases per side (INF → CAV → ARCH). A skill with `PHASE` trigger and 50% `RandomChanceCondition` therefore has 3 independent chances to proc per side per turn, like Petra's Evil EYe.  
`TURN_START_PER_TROOP` is sort of like `PHASE` in that it evals per troop type too, but timed differentyy during a battle, it evals at beginning of turn, before any attack phase takes plcase, and runs for every troop type present instead during every attack phase. very similar, except a `PHASE`-based skill will probably require a delay in order to be fair (if a skill effect is meant to benefit SELF_ARMY ie all your troop types).

---

## Conditions
Conditions for a skill to go through with activation and have it's effect or effects applied (i.e. go into SkillMod).  
All conditions are evaluated in sequence after the trigger fires. All must pass for the skill to activate.

```python
RandomChanceCondition(chance: float)        # fires if rng_fn() < chance  (0.5 = 50%)
RequiresTargetTroopType(troop_type)         # current attack target must be this troop type
RequiresFriendlyTroopType(troop_type)       # own troops of this type must have >=1 alive

# Planned:
RequiresTargetHasStatus(status_id: int)     # owner's active effects must contain an effect with the
                                            # matching status_id whose target_troop matches the
                                            # current enemy target (or is None)
```
`chance` param for `RandomChanceCondition` is optional and defaults to None. Can also be set via `SkillLevelData.chance` (which overrides `RandomChanceCondition.chance`), for skills where the trigger chance increases per skill level.  
If both are None, the condtion fails/returns FALSE.

Skills with no conditions always fire when their trigger fires.

---

## TargetScope

`target_scope` on `EffectSpec` resolves to a `TroopType` value during runtime and stored in `ActiveEffect.target_troop` (so the dynamic `CURRENT_TARGET` works), and used as a per-attack phase filter in `build_phase_ecs`.  
It does **not** determine which side hosts the effect — effects are always placed/hosted on the **skill owners side**.  
`target_scope` should always be `ENEMY_*`-types (or `None` which will default to all enemy troops, same as `ENEMY_ARMY`)

`benefactor_scope` should always be `SELF_*`-types (or `None` which will default to all own troops, same as `SELF_ARMY`) and restricts which own troop type benefits.

These 2 different scopes helps the engine apply skill effects in the SkillMod only  for during certain attack phases, like CAV vs ARCH, or any vs any etc.

Might need seperate classes for `SELF_*` types and `ENEMY_*` types, for proper type enforcemetn.

```
ENEMY_ARMY
  → target_troop = None (effect applies regardless of which enemy type is involved)

ENEMY_INFANTRY, ENEMY_CAVALRY, ENEMY_ARCHERS
  → target_troop = INF / CAV / ARCH (effect applies only when that enemy type is involved)

CURRENT_TARGET
  → resolves at apply-time to the concrete enemy type currently being attacked;
    locked into target_troop on the ActiveEffect

RANDOM_ENEMY_LINE
  → randomly selected live enemy troop type at apply-time. Don't think this exists in-game, but cool to have and try out.

SELF_ARMY, SELF_INFANTRY, SELF_CAVALRY, SELF_ARCHERS
  → used in benefactor_scope to restrict which own troop type benefits
```

A single `HeroSkillDefinition` can carry `EffectSpec`s with different scopes — each is placed and routed independently per phase.

---

## apply_delay

`EffectSpec.apply_delay` controls when the effect becomes active after the skill fires.

| Value | Behaviour |
|---|---|
| `0` (default) | Written to `active_effects` — effective this turn |
| `1` | Written to `pending_effects` — promoted to `active_effects` at turn end, effective next turn |

`apply_delay=1` is used whenever an effect should land during turn N but will activate during turn N+1.

Current implementation only suport 0 or 1 for values, since we don't track delays like we do remaining turns for `duration`. So apply_delay acts like a boolean currently, ie whether an effect go into either lists `*_active_effects` or `*_pending_effects` in BattleState.  
Don't think there's more than 1-turn delay currently observed, but if there are then should be fixed to properly track turn delays..some day :)

Maybe turn delays are a necessary side effect, if skills are rolled per attack phase and they want it to fairly benefit all troop types, so it's queued up for next turn if rolled true during say CAV attack phase, so it procs for all troop types during next turn...just a thought.

---

## Effect deduplication, for non-stackable skills

When `_apply_effect` is about to place an `ActiveEffect`, it first searches both the active and pending lists for the owner/hosts' side for an existing effect. The key used depends on `stack_rule`:

```
UNIQUE key:     (source_skill_id, effect_op)                      ← no target_troop
non-UNIQUE key: (source_skill_id, effect_op, target_troop)
```

`source_skill_id` — the skill definition `id` that triggered this application. Two different skills with the same `effect_op` always get different keys and never block each other.

`UNIQUE` -  only one instance of a given `(skill_id, effect_op)` pair can exist at all, regardless of which `target_troop` it was placed for. The first proc wins and locks in its target; any further procs this turn (from other attack phases or additional heroes with the same skill)..

If a matching key is found, `stack_rule` determines what happens:

| Rule | Existing found? | Outcome |
|---|---|---|
| `STACK` | no | new `ActiveEffect` created |
| `STACK` | yes | new `ActiveEffect` created anyway |
| `UNIQUE` | no | new `ActiveEffect` created |
| `UNIQUE` | yes | application discarded — first-proc target wins |
| `REFRESH` | no | new `ActiveEffect` created |
| `REFRESH` | yes | existing `remaining_turns` reset, no new instance |


`REFRESH` type probably doesnt exist in-game afaik, and it's currently not implemented correctly here, might change some day...
---

## SkillMod

THe damage coeffeicient we've come to know & love :)
Each attack phase gets a `SkillMod` multiplier applied to `compute_kills()`:

```
SkillMod = Numerator / Denominator

Numerator   = DamageUp × TroopDamageUp × OppDefenseDown
Denominator = DefenseUp × TroopDefenseUp × OppDamageDown
```

### Routing rules (per phase)

Effects are stored on the **owner's side**, ie the `host` of the skill. `build_phase_ecs` receives the current phase attacker's effect list and the current phase defender's effect list, routing by `effect_type`:

| Effect type | Read from | Condition | Routes to |
|---|---|---|---|
| `DAMAGE_UP`, `TROOP_DAMAGE_UP`, `OPP_DEFENSE_DOWN` | Phase attacker's active effects | Owner/host is the phase attacker | Numerator |
| `DEFENSE_UP`, `TROOP_DEFENSE_UP`, `OPP_DAMAGE_DOWN` | Phase defender's active effects | Owner/host is the phase defender | Denominator |

Since the two lists swap roles each time the attacking side flips, a hero with both `DAMAGE_UP` and `DEFENSE_UP` (e.g. Hilde) stores both on their own side and each is picked up at the right moment — `DAMAGE_UP` when their side is attacking, `DEFENSE_UP` when their side is defending.

Two additional troop-type filters apply after the type check:

**NUMERATOR** (from phase attacker's effects):
- `ae.target_troop` — must match `target_type` (the enemy type being attacked), or be `None`
- `benefactor_troop` — must match `att_type` (own troop type currently attacking), or be `None`

**DENOMINATOR** (from phase defender's effects):
- `ae.target_troop` — must match `att_type` (the enemy/attacker's troop type), or be `None`
- `benefactor_troop` — must match `target_type` (own troop type currently under attack), or be `None`

`effect_type` determines SkillMod numerator vs denominator placement and implicitly which phase direction (i.e Attacker or Defender) activates the effect. `target_scope` and `benefactor_scope` control *which specific troop matchup* within that direction triggers it.

---

## Composing Skills

### Example 1 — Permanent own-army buff (Amane, Chenko)

Single `EffectSpec`, `STATIC` trigger, permanent, `STACK` rule.

```python
HeroSkillDefinition(
    id=1001, name="Tri-Phalanx", trigger=TriggerType.STATIC,
    effects=[
        EffectSpec(EffectType.DAMAGE_UP, 102, TargetScope.ENEMY_ARMY),
    ],
    conditions=[],
    level_data={5: SkillLevelData(skill_id=1001, level=5, values={102: 25.0})},
)
```

At battle start (`TriggerType.STATIC`), one `ActiveEffect` is placed on the owner's/hosts side:
- `target_troop=None` — resolved from `TargetScope.ENEMY_ARMY`; passes the `build_phase_ecs` target filter for any enemy troop type
- `benefactor_troop=None` — no `benefactor_scope` set; passes the benefactor filter for any own attacking troop type
- `value=25.0`, `remaining_turns=-1` ie permanent

On every attack phase where ATTACKER is the phase attacker, `build_phase_ecs` reads `att_active_effects = attacker_active_effects`, finds `DAMAGE_UP op=102`, both filters pass → `+25%` goes to the numerator. Fires on all 3 of ATTACKER's attack phases each turn (INF, CAV, ARCH), against any enemy troop type still alive.

### Example 2 — Multi-effect skill (Hilde)

One `HeroSkillDefinition` with two `EffectSpec`s of different types. Both are stored on the owner's side; `effect_type` determines which phase direction each fires in.

```python
HeroSkillDefinition(
    id=2002, name="Noble Path", trigger=TriggerType.STATIC,
    effects=[
        EffectSpec(EffectType.DAMAGE_UP,  102, TargetScope.ENEMY_ARMY),
        EffectSpec(EffectType.DEFENSE_UP, 112, TargetScope.ENEMY_ARMY),
    ],
    conditions=[],
    level_data={5: SkillLevelData(skill_id=2002, level=5, values={102: 15.0, 112: 10.0})},
)
```

Both effects are stored on the **owner's side** ie skill host.  
If ATTACKER is phase attacker:  
`build_phase_ecs` reads `att_active_effects = attacker_active_effects` → finds `DAMAGE_UP op=102 +15%` → numerator. When DEFENDER attacks: `build_phase_ecs` reads `def_active_effects = attacker_active_effects` → finds `DEFENSE_UP op=112 +10%` → denominator. Hilde's defensive bonus reduces damage dealt *to her side*, not damage dealt *by* her side — the same list serves both directions.

### Example 3 — RNG attack-phase debuff with delay (Petra — Evil Eye)

`PHASE` trigger, `RandomChanceCondition`, `apply_delay=1`, `UNIQUE`. The 1-turn delay means the boost does not apply in the same turn it is placed.

```python
HeroSkillDefinition(
    id=3001, name="Evil Eye", trigger=TriggerType.PHASE,
    effects=[
        EffectSpec(
            EffectType.DAMAGE_UP, 102, TargetScope.CURRENT_TARGET,
            duration=1, apply_delay=1, stack_rule=StackRule.UNIQUE,
        ),
    ],
    conditions=[RandomChanceCondition(chance=0.5)],
    level_data={5: SkillLevelData(skill_id=3001, level=5, values={102: 50.0})},
)
```

**Walkthrough:** Turn N, INF phase — RNG passes → `_apply_effect` resolves `CURRENT_TARGET → target_troop=INF` → writes `ActiveEffect` to `attacker_pending_effects` (`host_side=ATTACKER, target_troop=INF, value=50.0`). At turn end, `_tick_statuses` promotes it to `attacker_active_effects`. Turn N+1 — when ATTACKER attacks, `build_phase_ecs` reads `att_active_effects = attacker_active_effects`, finds this effect. `DAMAGE_UP` → numerator check: `target_troop=INF == target_type=INF` → `+50%` added. After turn N+1 ends, `remaining_turns` decrements 1 → 0 → removed.

UNIQUE dedup key (no `target_troop`): `(3001, 102)`. A second proc in the same turn — from a CAV or ARCH phase, or a second Petra — searches `attacker_active_effects + attacker_pending_effects`, finds the pending instance by `(source_skill_id=3001, effect_op=102)`, and is discarded. The first proc's `target_troop` is locked in. Multiple Petras increase per-turn proc probability without stacking instances. Note that rolls and procs (actual placements) have independent counters — multiple rolls can succeed in one turn, but only 1 placement ever happens.

### Example 4 — Troop skills

Regular non-RNG troop skills can use `TURN_START` trigger and `duration=1` — the engine places a fresh `ActiveEffect` each turn, which is removed at turn end when `remaining_turns` ticks to 0. Target/benefactor filtering works identically to hero skills via `target_scope` and `benefactor_scope` on `EffectSpec`.

One could also give them `STATIC` trigger type and `duration=-1`, depending on how we watn them to be counted in skill/effect triggers/activations.

RNG-troop skills should have `TURN_START_PER_TROOP` or `PHASE` trigger type, and `chance` set in `EffectSpec`

```python
# TURN_START, duration=1: +10% TROOP_DAMAGE_UP vs enemy CAV, only for own INF phases
TroopSkillDefinition(
    id=1301, name="Master Brawler", trigger=TriggerType.TURN_START,
    effects=[EffectSpec(
        EffectType.TROOP_DAMAGE_UP, 301, TargetScope.ENEMY_CAVALRY,
        benefactor_scope=TargetScope.SELF_INFANTRY, duration=1,
    )],
    conditions=[],
    level_data={1: SkillLevelData(skill_id=1301, level=1, values={301: 10.0})},
)
```

Both eg T6 INF and T10 INF may carry the same skill in their definition, but `ArmyLine.troop_skills` dedupes by `skill.id` before the engine sees the list, so the engine always receives at most one instance per unique troop skill ID and stacking doesnt apply.

Note: `TROOP_DAMAGE_UP` and `TROOP_DEFENSE_UP` are exclusive to troop skills. Hero skills use `DAMAGE_UP` / `DEFENSE_UP` etc. According to Daryl troop skills goes into Skillmod as well, but their own separate effect_op's so they'll always stack multiplicitavely with hero skills.  
Here i decided to invent for them their own effect_type too, in order to ensure that structuraly.

### Example 5 — Benefactor-restricted effect

An effect that only benefits a specific own troop type. `benefactor_scope` adds a second filter in `build_phase_ecs` after the target check.

```python
HeroSkillDefinition(
    id=9099, name="...", trigger=TriggerType.PHASE,
    effects=[
        EffectSpec(
            EffectType.DAMAGE_UP, 101, TargetScope.CURRENT_TARGET,
            benefactor_scope=TargetScope.SELF_CAVALRY,
            duration=1, apply_delay=1, stack_rule=StackRule.UNIQUE,
        ),
    ],
    ...
)
```

Without `benefactor_scope`, all own troop types benefit ie same as `SELF_ARMY`.  
With `SELF_CAVALRY`, only your CAV attack phases pass the benefactor check in `build_phase_ecs`, meaning the DamageUp will only be applied in your SkillMod numerator when your CAV attacks an enemy troop type (and with `TargetScope.CURRENT_TARGET` the target_troop type would be dynamic, meaning it might not be according to default targeting order since it's decided at runtime).

---

## Engine Responsibilities

### SkillEngine
- `evaluate_skills(hero_skills, troop_skills, trigger, context)` — evaluates hero and troop skills for the given trigger; writes `ActiveEffect`s to the owners/hosts' side in `BattleState`
- `build_phase_ecs(att_active_effects, def_active_effects, att_troop_type, target_troop_type)` — routes each `ActiveEffect` to SKillmod numerator or denominator EffectCollection for the current attack phase; returns `(numerator_ec, denominator_ec)`
- `collect_retarget(troop_skills, context)` — evaluates `TROOP_SPECIAL` / `RETARGET` troop skills; used by battle engine before attack phases to pre-compute CAV targeting.
- `compute_skill_mod(numerator_ec, denominator_ec)` — returns SkillMod float

Does not calculate damage, kill troops, or manage turn state.

### BattleEngine
- Runs the turn loop, invokes the skill engine at different trigger points to evaluate skills.
- Pre-computes targets for both sides before their attack phases (including CAV RETARGET roll)
- Calls `compute_kills()` with SkillMod per attack phase
- Accumulates `pending_losses`, applies them simultaneously at turn end.
- Ticks effects at turn end: decrement `remaining_turns` on active effects first, then promote `pending_effects → active_effects`
- Snapshots state each turn; determines winner

---

## TODO

- **`EveryNTurns(N)` trigger type** — fires on turns where `state.turn % N == 0` (first fires on turn N, not turn 1). Needed for Sophia's Deathblow and Alcar's Rescuing Hands.
- **Counter-based triggers** ("every N attacks by my CAV" — Ancestral Guidance)
- **Extra attack phase** (Yang-style "additional strike", but also Archer speci skill Volley maybe, seems functonally simimlar)
- **Direct-damage / troop-kill skills** that seems to account for a direct numer of enemy troop kills
- **Battle reporting counters** (indepedent counting for roll count, actual placement count, etc.)
