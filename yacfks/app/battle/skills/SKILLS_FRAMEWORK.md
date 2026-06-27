# Skills & Battle Engine Reference

## Core Philosophy

Skills are pure data. The battle engine drives the turn loop; the skill engine reacts to it. No hero- or troop-specific logic lives in the engines — everything is expressed by composing a small set of building blocks.

A hero skill is: a trigger + conditions + one or more `StatusApplication`s.  
A status is: a duration + stack rule + one or more `SkillEffect`s.  
A troop skill is: a trigger + conditions + one or more `SkillEffect`s (direct routing, no status layer).

---

## Architecture Overview

```
Battle engine fires trigger event
  ↓
SkillEngine.collect_effects(trigger, context)
  ├─ For each hero skill: _apply_hero_skill
  │    → check trigger + conditions + level data
  │    → _apply_status(StatusApplication) → writes ActiveStatus to BattleState
  │         apply_delay=0 → active_statuses  (effective this turn)
  │         apply_delay=1 → pending_statuses (effective next turn)
  │
  └─ For each troop skill: _apply_troop_skill
       → check trigger + conditions + level data
       → route SkillEffect directly to phase numerator_ec / denominator_ec

Per attack phase:
  SkillEngine.collect_phase_effects(active_statuses, att_side, att_type, def_side, target_type)
    → reads every ActiveStatus, routes each SkillEffect to numerator_ec or denominator_ec
  SkillEngine.compute_skill_mod(numerator_ec, denominator_ec)
    → returns SkillMod float → battle engine feeds into compute_kills()
```

---

## Data Models

Models are listed in dependency order.

### SkillEffect

The atomic combat modifier. Lives inside `StatusDefinition.effects` (hero path) and `TroopSkill.effects` (troop path).

```python
SkillEffect:
    effect_type:      EffectType          # DAMAGE_UP | DEFENSE_UP | TROOP_DAMAGE_UP | TROOP_DEFENSE_UP
                                          # OPP_DEFENSE_DOWN | OPP_DAMAGE_DOWN | RETARGET
    effect_op:        int                 # stacking slot — same op = additive, different op = multiplicative
    scope:            TargetScope         # routing scope (see TargetScope section)
    benefactor_scope: TargetScope | None  # restricts which own troop type benefits from enemy-side effects; None = all
```

`effect_op` IDs should be globally unique. Hero skill ops and troop skill ops are in separate ID ranges so they always stack multiplicatively against each other.

### SkillLevelData

Numeric values for a skill at a specific level. The `SkillEffect` template carries no numbers — this is where they live.

```python
SkillLevelData:
    skill_id: int
    level:    int
    values:   dict[int, float]   # effect_op → percentage value (e.g. {102: 25.0} means op 102 = +25%)
```

### StatusDefinition

Immutable template describing what a status IS. Registered at import time via `register_status()`.

```python
StatusDefinition:
    id:          int               # globally unique
    name:        str
    duration:    int               # turns active; -1 = permanent (entire battle)
    effects:     list[SkillEffect] # what this status contributes per phase (no values here)
    stack_rule:  StackRule         # STACK | UNIQUE | REFRESH | REPLACE
    apply_delay: int = 0           # 0 = active this turn; 1 = active next turn
```

`StatusDefinition` holds **no numeric values** — those are resolved at apply-time from `SkillLevelData` and stored on the live `ActiveStatus`.

### StatusApplication

Pairs a `StatusDefinition` with a placement scope. Used in `HeroSkillDefinition.status_applications`.

```python
StatusApplication:
    status: StatusDefinition
    scope:  TargetScope        # placement scope — determines which side and troop HOST the status
```

This is distinct from the routing scopes on `StatusDefinition.effects`. Placement answers "where does the status go?"; routing answers "which phases does each effect contribute to?"

### ActiveStatus

A live status instance tracked in `BattleState`. Self-contained — everything needed to evaluate it per phase is on the instance.

```python
ActiveStatus:
    definition:      StatusDefinition
    remaining_turns: int
    source_skill_id: int
    target_side:     BattleSide         # which side's troops HOST this status (resolved at apply-time)
    target_troop:    TroopType | None   # specific troop type, or None = all troops on that side
    effect_values:   dict[int, float]   # effect_op → resolved numeric value
```

`target_side` and `target_troop` are the resolved, concrete form of `StatusApplication.scope` at the moment the skill fired. For `CURRENT_TARGET`, this locks in the actual troop type that was being targeted when the curse was applied — it does not update if the target changes later.

### HeroSkillDefinition

Defines everything about a hero skill: when it fires, under what conditions, and which statuses it writes.

```python
HeroSkillDefinition:
    id:                   int
    name:                 str
    trigger:              TriggerType
    status_applications:  list[StatusApplication]
    conditions:           list[SkillCondition]
    level_data:           dict[int, SkillLevelData] | None
```

### TroopSkill

A troop skill that contributes effects directly to the phase `EffectCollection` without going through the status layer.

```python
TroopSkill:
    id:         int
    name:       str
    trigger:    TriggerType
    effects:    list[SkillEffect]
    conditions: list[SkillCondition]
    level_data: dict[int, SkillLevelData] | None
```

---

## Trigger Types

| Trigger      | When it fires                                     | Used by |
|---|---|---|
| `ALWAYS`     | Once per battle, before turn loop starts          | Hero skills (permanent buffs) |
| `TURN_START` | Once per turn, both sides                         | Hero skills (per-turn re-apply) |
| `ATTACK`     | Once per attack phase (per troop type, per side)  | Hero skills (RNG procs), troop skills |

`ATTACK` fires 6 times per turn total — 3 phases per side (INF/CAV/ARCH). A skill with `ATTACK` trigger and 50% `RandomChanceCondition` therefore has 3 independent chances to proc per side per turn.

Both sides execute all three of their attack phases each turn. "Attacking side" in any given phase is the side currently running its phase loop — not necessarily `BattleSide.ATTACKER`.

---

## Conditions

All conditions are evaluated in sequence after the trigger fires. All must pass for the skill to activate.

```python
RandomChanceCondition(chance: float)         # fires if rng_fn() < chance (e.g. 0.5 = 50%)
RequiresTargetTroopType(troop_type)          # current attack target must be this troop type
RequiresFriendlyTroopType(troop_type)        # own troops of this type must have at least 1 alive
```

Skills with no conditions always fire when their trigger fires.

---

## TargetScope

`TargetScope` serves two distinct roles depending on context:

**Placement scope** (`StatusApplication.scope`):  
Determines which side and troop type HOST the resulting `ActiveStatus`. Resolved once when the skill fires.

**Routing scope** (`SkillEffect.scope`):  
Determines how the effect is routed per phase: numerator vs denominator, and which troop type filter applies.

`SELF_*` and `ENEMY_*` are always **relative to the skill's source side** at the time it fires, not to a fixed "attacker" or "defender" slot in the battle. This matters because both sides fire skills — a defender's `SELF_ARMY` buff is placed on the defender's troops.

```
SELF_ARMY, SELF_INFANTRY, SELF_CAVALRY, SELF_ARCHERS
  → own side's troops (all or specific type)

ENEMY_ARMY, ENEMY_INFANTRY, ENEMY_CAVALRY, ENEMY_ARCHERS
  → opposing side's troops (all or specific type)

CURRENT_TARGET
  → whichever enemy troop type is the current attack target at apply-time;
    locks in to a concrete TroopType on ActiveStatus.target_troop

RANDOM_ENEMY_LINE
  → randomly selected live enemy troop type at apply-time
```

A single `StatusDefinition` can carry effects with **different scopes** — for example, a status that applies a 20% defense bonus only to own infantry and a 30% bonus only to own cavalry. Each effect is routed independently per phase (Triton/Thrud patterns, see Composition section).

---

## apply_delay

`StatusDefinition.apply_delay` controls when the status becomes active after the skill fires.

| Value | Behaviour |
|---|---|
| `0` (default) | Written to `active_statuses` — effective this turn |
| `1` | Written to `pending_statuses` — promoted to `active_statuses` at turn end, effective next turn |

`apply_delay=0` covers most cases: own-side buffs, any effect that should take hold immediately.  
`apply_delay=1` is the standard for enemy curses — matches the game's behaviour where a curse lands during turn N and contributes to damage starting in turn N+1.

`apply_delay` is explicit on `StatusDefinition` and **not** inferred from scope. An own-side buff can delay, and an enemy-side curse can be immediate — the engine honours whichever value is set.

---

## SkillMod

Each attack phase gets a `SkillMod` multiplier applied to `compute_kills()`:

```
SkillMod = Numerator / Denominator

Numerator   = DamageUp × TroopDamageUp × OppDefenseDown
Denominator = DefenseUp × TroopDefenseUp × OppDamageDown
```

### Routing rules (per phase)

`collect_phase_effects` evaluates every `ActiveStatus` for the current phase `(att_side, att_type → def_side, target_type)`:

| Effect type | Status on | Effect scope | Troop filter | Routes to |
|---|---|---|---|---|
| Numerator types | `att_side` | `SELF_*` | scope troop == `att_type` (or scope is SELF_ARMY) | numerator |
| Numerator types | `def_side` | `ENEMY_*` / `CURRENT_TARGET` | scope troop == `target_type` (or ENEMY_ARMY) | numerator |
| Denominator types | `def_side` | `SELF_*` | scope troop == `target_type` (or SELF_ARMY) | denominator |

For enemy-side numerator effects, `benefactor_scope` applies a second filter: if set, only the specified own troop type's attack phases pick up the bonus (e.g. `SELF_ARCHERS` = only ARCH phases benefit from the curse). `None` means all own troop types benefit.

---

## Stacking

Within each effect type group, stacking is determined by `effect_op`:

- **Same `effect_op`** → additive: `25% + 25% = +50% → ×1.50`
- **Different `effect_op`** → multiplicative: `×1.50 × ×1.50 = ×2.25`

This means two heroes of the same type share the same op and stack additively; two heroes of different types use different ops and stack multiplicatively.

**Example — 2× Chenko (op=101, +25%) and 2× Amane (op=102, +25%):**
```
DamageUp op=101: 25+25 = +50% → ×1.50
DamageUp op=102: 25+25 = +50% → ×1.50
Combined DamageUp = 1.50 × 1.50 = ×2.25
```

**Example — 3× Saul (op=112 +10%, op=113 +15%) and 1× Hilde (op=112 +10%, op=102 +15%):**
```
DefenseUp op=112: 10+10+10+10 = +40% → ×1.40   (3 Saul + 1 Hilde, additive)
DefenseUp op=113: 15+15+15    = +45% → ×1.45   (3 Saul, separate multiplier)
DamageUp  op=102: 15          = +15% → ×1.15   (Hilde only, routes to numerator)
```
Hilde's two effects route to opposite sides of SkillMod — `DamageUp` boosts the numerator when Hilde's side attacks; `DefenseUp` boosts the denominator when the enemy attacks Hilde's troops.

### Status stack rules

When the same status would be applied to the same `(target_side, target_troop)` again:

| Rule | Behaviour |
|---|---|
| `STACK` | Add a new instance — values accumulate across both instances |
| `UNIQUE` | Discard the new application — first instance wins |
| `REFRESH` | Reset `remaining_turns` on the existing instance |
| `REPLACE` | Remove the existing instance, add the new one |

---

## Composing Skills

### Pattern 1 — Permanent own-army buff (Amane, Chenko)

Single effect, ALWAYS trigger, full battle duration, STACK rule (each hero instance stacks additively via same op).

```python
AMANE_BUFF = register_status(StatusDefinition(
    id=1001, name="Tri-Phalanx", duration=-1,
    effects=[SkillEffect(EffectType.DAMAGE_UP, op=102, scope=TargetScope.SELF_ARMY)],
    stack_rule=StackRule.STACK,
))

_amane_tri_phalanx = HeroSkillDefinition(
    id=1001, name="Tri-Phalanx", trigger=TriggerType.ALWAYS,
    status_applications=[StatusApplication(AMANE_BUFF, TargetScope.SELF_ARMY)],
    conditions=[],
    level_data={5: SkillLevelData(skill_id=1001, level=5, values={102: 25.0})},
)
```

Placement scope and effect routing scope are both `SELF_ARMY` here — the status lands on own troops and the effect routes to the numerator when own troops attack.

### Pattern 2 — Multi-effect status (Saul, Hilde)

One status with two effects, different op IDs → two independent stacking slots. Effects can route to numerator and denominator simultaneously.

```python
HILDE_BUFF = register_status(StatusDefinition(
    id=2002, name="Noble Path", duration=-1,
    effects=[
        SkillEffect(EffectType.DAMAGE_UP,  op=102, scope=TargetScope.SELF_ARMY),  # → numerator
        SkillEffect(EffectType.DEFENSE_UP, op=112, scope=TargetScope.SELF_ARMY),  # → denominator
    ],
    stack_rule=StackRule.STACK,
))
```

### Pattern 3 — Troop-scoped effects (Triton / Thrud)

One status whose effects each carry a specific-troop scope. Each effect is routed independently — only phases involving that troop type pick it up.

```python
# Triton-like: different defense bonus per troop type
OATH_BUFF = register_status(StatusDefinition(
    id=9001, name="Oath", duration=-1,
    effects=[
        SkillEffect(EffectType.DEFENSE_UP, op=301, scope=TargetScope.SELF_INFANTRY),  # only when INF is attacked
        SkillEffect(EffectType.DEFENSE_UP, op=302, scope=TargetScope.SELF_CAVALRY),
        SkillEffect(EffectType.DEFENSE_UP, op=302, scope=TargetScope.SELF_ARCHERS),   # CAV and ARCH share op → additive
    ],
    stack_rule=StackRule.STACK,
))

# Thrud-like: offense AND defense for specific troop types only
HUNGER_BUFF = register_status(StatusDefinition(
    id=9002, name="Hunger", duration=-1,
    effects=[
        SkillEffect(EffectType.DAMAGE_UP,  op=401, scope=TargetScope.SELF_INFANTRY),  # INF and ARCH share op
        SkillEffect(EffectType.DAMAGE_UP,  op=401, scope=TargetScope.SELF_ARCHERS),
        SkillEffect(EffectType.DEFENSE_UP, op=402, scope=TargetScope.SELF_INFANTRY),
        SkillEffect(EffectType.DEFENSE_UP, op=402, scope=TargetScope.SELF_ARCHERS),
    ],
    stack_rule=StackRule.STACK,
))
```

### Pattern 4 — RNG attack curse (Petra)

`ATTACK` trigger, `RandomChanceCondition`, enemy-side status with `apply_delay=1` (curse is active next turn), `UNIQUE` (one curse per target).

```python
CURSED = register_status(StatusDefinition(
    id=3001, name="Cursed", duration=1, apply_delay=1,
    effects=[SkillEffect(EffectType.DAMAGE_UP, op=103, scope=TargetScope.CURRENT_TARGET)],
    stack_rule=StackRule.UNIQUE,
))

_petra_evil_eye = HeroSkillDefinition(
    id=3001, name="Evil Eye", trigger=TriggerType.ATTACK,
    status_applications=[StatusApplication(CURSED, scope=TargetScope.CURRENT_TARGET)],
    conditions=[RandomChanceCondition(chance=0.5)],
    level_data={5: SkillLevelData(skill_id=3001, level=5, values={103: 50.0})},
)
```

**Walkthrough:** Turn N, INF phase — RNG hits → CURSED written to `pending_statuses` with `target_side=DEF, target_troop=INF`. At turn end, `_tick_statuses` promotes it to `active_statuses`. Turn N+1 — all three of ATT's attack phases targeting DEF INF pick up `DAMAGE_UP op=103 +50%` in the numerator.

### Pattern 5 — Troop skill with condition

Troop skills bypass the status layer and route directly to the phase EC. Conditions (typically `RequiresTargetTroopType`) gate them.

```python
_INF_ANTI_CAV = TroopSkill(
    id=201, name="Anti-Cavalry Charge", trigger=TriggerType.ATTACK,
    effects=[SkillEffect(EffectType.TROOP_DAMAGE_UP, op=201, scope=TargetScope.SELF_ARMY)],
    conditions=[RequiresTargetTroopType(TroopType.CAV)],
    level_data={1: SkillLevelData(skill_id=201, level=1, values={201: 10.0})},
)
```

Only fires when the current attack target is CAV. The effect goes straight to `numerator_ec` — no status is written to `BattleState`.

### Pattern 6 — Benefactor-restricted curse (hypothetical)

A curse that only benefits a specific troop type on the attacker's side. `benefactor_scope` on the `SkillEffect` adds a second filter after the enemy-side troop filter.

```python
ARCH_CURSE = register_status(StatusDefinition(
    id=9099, name="ArchFocus", duration=1, apply_delay=1,
    effects=[SkillEffect(
        EffectType.DAMAGE_UP, op=199,
        scope=TargetScope.CURRENT_TARGET,
        benefactor_scope=TargetScope.SELF_ARCHERS,  # only own ARCH attack phases benefit
    )],
    stack_rule=StackRule.UNIQUE,
))
```

Without `benefactor_scope` (i.e. `None`), all of the attacker's troop types benefit when they hit the cursed troop. With `benefactor_scope=SELF_ARCHERS`, only the ARCH phase picks up the bonus.

---

## Engine Responsibilities

### SkillEngine
- `collect_effects(trigger)` — evaluates hero and troop skills, applies statuses, returns direct-routed EC
- `collect_phase_effects(active_statuses, ...)` — routes active status effects to numerator/denominator EC
- `compute_skill_mod(numerator_ec, denominator_ec)` — returns SkillMod float

Does **not** calculate damage, kill troops, or manage turn state.

### BattleEngine
- Runs the turn loop: ALWAYS (once) → per turn: TURN_START → 3× ATTACK per side
- Determines target via priority: INF → CAV → ARCH
- Calls `compute_kills()` with SkillMod per phase
- Accumulates `pending_losses`, applies them simultaneously at turn end
- Ticks statuses at turn end (`pending → active`, decrement `remaining_turns`)
- Snapshots state each turn; determines winner

Treats skills as a black box: asks "what SkillMod applies to this phase?" and feeds the answer to the damage formula.

---

## What's Not Yet Implemented

- Counter-based triggers ("every N attacks by my CAV")
- `TurnNumberCondition` ("only fires on turn 1–5")
- `StatusPresentCondition` ("only fires if target already has status X")
- Yang's extra attack phase
- Migrating troop skills to the status model (T7 RETARGET especially)
- `ATTACKER_OF_STATUS_TARGET` / `DEFENDER_OF_STATUS_TARGET` scopes
