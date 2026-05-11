# Battle System

## Overview

The battle system is a turn-based combat system accessed when the player encounters enemies on the overworld. It uses a round-based system where the player selects actions for all party members, then enemies select actions, and all actions are executed in order of speed (priority).

```
BATTLE FLOW:
┌─────────────────────────────────────────────────────────────┐
│  1. PARTY COMMAND - Choose FIGHT/MAGIC/ITEM/RUN            │
│         ↓                                                   │
│  2. PARTY TARGET - Select enemy target (FIGHT only)        │
│         ↓                                                   │
│  Auto-advance to next living party member                  │
│         ↓                                                   │
│  Repeat until all living members have acted                │
│         ↓                                                   │
│  3. PREPARE BATTLE - Queue all actions sorted by speed     │
│         ↓                                                   │
│  4. EXECUTE - Process each action in priority order        │
│         ↓                                                   │
│  5. Check victory/defeat or return to step 1               │
└─────────────────────────────────────────────────────────────┘
```

## Controls

- UP/DOWN: Navigate menu options
- Z: Select / Confirm
- X: Back / Cancel

## State Machine

| State | Description |
|-------|-------------|
| `party_command` | Player chooses action for current member |
| `party_spell` | Player selects spell to cast |
| `party_target` | Player selects target (enemy or ally) |
| `execute` | Actions are processed in speed order |
| `flash` | Attacker highlight animation before action |
| `message` | Display battle messages |
| `victory` | All enemies defeated |
| `defeat` | All party members fallen |

## Data Structures

### Party Member

```python
{
    "name": str,        # Character name
    "hp": int,          # Current HP
    "hp_max": int,      # Maximum HP
    "mp": int,          # Current MP
    "mp_max": int,      # Maximum MP
    "atk": int,         # Attack power
    "def": int,         # Defense
    "spd": int,         # Speed (determines turn order)
    "alive": bool,      # Living status
    "spells": list     # List of spell IDs (e.g., ["fire", "cure"])
}
```

### Enemy

```python
{
    "id": str,          # Enemy type ID
    "name": str,
    "hp": int,
    "hp_max": int,
    "atk": int,
    "def": int,
    "spd": int,
    "xp": int,          # Experience reward
    "gold": int,        # Gold reward
    "alive": bool
}
```

### Action (in queue)

```python
{
    "type": "party_attack" | "party_magic" | "enemy_attack",
    "name": str,
    "atk": int,                     # For attacks
    "spell_id": str,                # For magic
    "spell_name": str,              # For magic
    "target": int,                  # Target index
    "speed": int                    # For sorting
}
```

### Spell Types

| Type | Target | Effect |
|------|--------|--------|
| attack | enemy | Deals magic damage (power - enemy def) |
| heal | ally | Restores HP (power amount) |
| revive | ally | Revives with HP (power amount) |
| cure_status | ally | Removes status ailments |
| buff | ally | Applies positive status |
| debuff | enemy | Applies negative status |

## SpeedQueue Class

A priority queue that automatically sorts actions by speed (highest first).

```python
class SpeedQueue:
    def add(self, action):    # Adds and sorts by speed
    def pop(self):            # Returns highest speed action
    def clear(self):          # Empties queue
    def __len__(self):        # Returns queue length
```

## Battle Flow Details

The battle flow is streamlined - player goes through each living party member in order, giving commands to each.

### 1. Party Command Phase

Battle starts immediately showing the first living party member's command menu.
- Choose from: FIGHT, MAGIC, ITEM, RUN
- MAGIC shows spell list if party member has spells
- ITEM not yet implemented
- RUN attempts to escape (50% success rate)
- Press X to go back (clears any action already selected)

### 2. Party Spell Selection (MAGIC)

- Shows available spells for current party member
- Each spell shows name and MP cost
- Spells grayed out if not enough MP
- UP/DOWN to navigate, Z to select, X to go back

### 3. Party Target Phase

- For FIGHT: select enemy target
- For MAGIC: select enemy (attack spells) or ally (heal/revive spells)
- Navigate between living targets
- Yellow outline highlights selected target
- Press Z to confirm, X to go back

### 3. Auto-Advance to Next Character

After confirming a target, automatically moves to the next living party member who hasn't acted yet. Shows "READY" indicator for members who have already chosen their action.

### 4. Prepare Battle

When all living party members have selected actions:
- Build action queue with all party member actions
- Computer selects random target for each living enemy
- All actions sorted by speed (highest first)
- Enter execute phase

### 5. Execute Phase

- Process one action at a time
- Display damage message for 1 second
- If target is dead, automatically retarget to next living opponent
- After all actions processed, return to party selection
- Check for victory/defeat after each action or at round end

### Action Animation

When an action executes:
1. Attacker flashes 4 times (alternating highlight)
2. Yellow flash for party members, red flash for enemies
3. Each flash lasts 0.15 seconds
4. Then damage message appears

## Damage Calculation

```python
def calc_damage(atk, def_):
    return max(1, atk - def_)
```

Minimum damage is always 1.

## Victory/Defeat

- **Victory**: Triggered when all enemies are dead
  - Display XP and gold rewards
  - Each living party member gains full XP amount
  - Level up system: when XP >= XP_next, character levels up
  - Level up bonuses: +5 HP_max, +2 ATK, +1 DEF, XP_next * 1.5
  - Awards gold to player
  - Press Z to return to overworld

- **Defeat**: Triggered when all party members are dead
  - Display "DEFEAT" message
  - Press Z to revive all party members and return to title screen

## Party Member Stats

| Field | Description |
|-------|-------------|
| name | Character name |
| hp | Current HP |
| hp_max | Maximum HP |
| atk | Attack power |
| def | Defense |
| spd | Speed (determines turn order) |
| alive | Living status |
| level | Current level |
| xp | Current XP |
| xp_next | XP needed for next level |

Default party stats:
- Warrior: HP 50, MP 0, ATK 12, DEF 5, SPD 10, Spells: none
- Wizard: HP 35, MP 30, ATK 6, DEF 2, SPD 8, Spells: fire, ice, thunder, cure
- Rogue: HP 40, MP 0, ATK 10, DEF 4, SPD 12, Spells: none
- Healer: HP 30, MP 40, ATK 6, DEF 3, SPD 6, Spells: cure, raise, esuna

All start at Level 1 with 0 XP, 100 XP_next.

## Enemy Data

Enemies are defined in `data/enemies.json`:

```json
{
  "enemies": {
    "enemy_id": {
      "name": "Display Name",
      "hp": 20,
      "hp_max": 20,
      "atk": 5,
      "def": 2,
      "spd": 6,
      "xp": 10,
      "gold": 5
    }
  },
  "encounters": {
    "map_id": ["enemy1", "enemy2", ...]
  }
}
```

### Current Enemies

| ID | Name | HP | ATK | DEF | SPD | XP | Gold |
|----|------|-----|-----|-----|-----|-----|------|
| goblin | Goblin | 20 | 5 | 2 | 6 | 10 | 5 |
| skeleton | Skeleton | 30 | 8 | 4 | 5 | 20 | 12 |
| slime | Slime | 12 | 3 | 1 | 4 | 5 | 3 |
| wolf | Wolf | 25 | 7 | 3 | 9 | 15 | 8 |
| imp | Imp | 18 | 6 | 2 | 8 | 12 | 7 |
| mage | Dark Mage | 35 | 12 | 5 | 7 | 35 | 25 |

### Default Party

| Name | HP | ATK | DEF | SPD |
|------|-----|-----|-----|-----|
| Warrior | 50 | 12 | 5 | 10 |
| Wizard | 35 | 15 | 2 | 8 |
| Rogue | 40 | 10 | 4 | 12 |
| Healer | 30 | 6 | 3 | 6 |

## Encounter Generation

- Random 1-2 enemies per encounter (from map's encounter list)
- If map has no encounters, uses all available enemies
- Map IDs: overworld_1, overworld_2, overworld_3, town_1, dungeon_1

## Drawing Layout

```
+----------------------------------+
|           ENEMY AREA             |
|   [Enemy 1]  [Enemy 2]  [Enemy3]|
|   HP: 20/20   HP: 12/12         |
+----------------------------------+
|           MESSAGE BOX            |
+----------------------------------+
|     PARTY STATUS / COMMANDS      |
| [Member1] [Member2] [Member3]  |
| HP: 50/50  HP: 35/35            |
+----------------------------------+
|  Command Bar (when active)      |
| FIGHT  MAGIC  ITEM  RUN          |
+----------------------------------+
```

- Enemy area: top 75% of screen
- Party area: bottom 25% of screen
- Message box: centered overlay
- Command bar: bottom 25% when active

## Implementation Notes

- `party_actions` dict stores {member_index: action} for current round
- `action_queue` is SpeedQueue containing all actions for the round
- Dead targets are skipped during execution but actions still consumed
- After all actions processed, battle returns to party selection for next round
- Victory/defeat can trigger mid-round or at round end

## Message Queue

When an action kills a target, multiple messages may be generated (e.g., "X attacks for Y damage!" followed by "Target is slain!"). These are stored in `_message_queue` and displayed sequentially:

- First message is shown immediately (1 second duration)
- Subsequent messages shown after timer expires
- Death messages (e.g., "Goblin is slain!") are queued in `_message_queue`
- When message timer expires or player presses Z, next queued message is shown

### Victory/Defeat Timing

Victory/defeat is checked IMMEDIATELY when an action kills the last target:
- When last enemy dies: action queue is cleared, victory state triggered
- When last party member falls: action queue is cleared, defeat state triggered
- This prevents remaining queued actions from executing after battle ends
- The death message still shows before the victory/defeat screen

## Target Retargeting

When a targeted enemy dies during battle:
- If the attacker is a party member: retarget to first living enemy
- If the attacker is an enemy: retarget to first living party member
- If no living targets remain, action is skipped and next action proceeds

## Equipment and Stats

Party member stats are calculated from base values + equipment bonuses:

```python
def calc_party_stats(party):
    base_atk = member.get("atk", 10)
    base_def = member.get("def", 5)
    atk_bonus = weapon.atk + armor.atk  # etc
    member["atk"] = base_atk + atk_bonus
    member["def"] = base_def + def_bonus
```

This is called when loading a save or starting a new game, ensuring equipped weapons and armor affect battle damage.

## Current Implementation Issues

- All party members can target same enemy - no automatic distribution
- Spell messages could have different timing than attacks

---

# Battle System Refactoring Plan

## Problem Statement

The current battle system has grown into a monolithic ~820 line class that is difficult to maintain and extend. Adding new features causes breakage in multiple places, and the code feels "clunky" to work with.

Key issues:
1. Single class handles state transitions, combat logic, AND rendering
2. Implicit dict structures instead of typed objects
3. Duplicated logic scattered throughout
4. Inconsistent field naming (`level` vs `lvl`, `xp` vs `exp`)

## Architecture Goals

- **Separation of Concerns**: Split model (combat logic) from view (rendering) from controllers (input handling)
- **Type Safety**: Use dataclasses/enums instead of implicit dicts
- **Testability**: Make components independently testable
- **Maintainability**: Each piece can be modified without breaking others

## New File Structure

```
game/
├── battle/
│   ├── __init__.py           # Exports for game/battle module
│   ├── model.py              # BattleModel: combat logic, state
│   ├── states.py             # BattleState handlers (input per state)
│   ├── renderer.py           # BattleRenderer: all draw logic
│   ├── dataclasses.py        # Actor, Action, Spell, BattleEvent
│   └── engine.py             # Helpers (damage calc, speed queue)
└── scenes/
    └── battle.py             # Thin coordinator, registers scene
```

### Responsibilities

**dataclasses.py**
- `Actor` - party member or enemy with all stats
- `ActionType` - enum (ATTACK, MAGIC, ENEMY_ATTACK, etc.)
- `Action` - typed action object
- `BattleEvent` - results from processing (damage, death, etc.)

**model.py**
- `BattleModel` class with:
  - party: list[Actor]
  - enemies: list[Actor]
  - action_queue: SpeedQueue
  - process_action() -> list[BattleEvent]
  - check_victory/defeat() -> bool

**states.py**
- `BattleState` - abstract base
- `CommandState`, `SpellState`, `TargetState`, `ExecuteState`, etc.
- Each handles its own input + update logic
- Communicates with model to queue actions

**renderer.py**
- `BattleRenderer` - all draw_* methods
- Text caching, scale handling
- Receives model state to render

**scenes/battle.py**
- Scene registration only
- Coordinates model, states, renderer
- Handles scene lifecycle (on_enter, on_exit)

## Field Naming Standard

All code uses consistent field names matching the engine defaults:

| Field | Usage |
|-------|-------|
| `lvl` | Current level |
| `exp` | Current XP |
| `exp_next` | XP needed for next level |
| `hp`, `hp_max` | Health |
| `mp`, `mp_max` | Magic points |
| `atk`, `def_` | Attack / Defense (def_ to avoid Python keyword) |
| `spd` | Speed |
| `alive` | Boolean survival state |

## Implementation Phases

### Phase 1: Infrastructure
- Create `game/battle/` directory
- Add dataclasses for Actor, Action, ActionType, BattleEvent
- Move `calc_damage()` and `SpeedQueue` to `engine.py`

### Phase 2: Model Extraction
- Build `BattleModel` class with all combat logic
- Dual-write: keep old code calling model to verify
- Verify behavior unchanged

### Phase 3: State Handlers
- Extract each state into handler classes
- Replace if/elif chains with `state.update(dt)`

### Phase 4: Renderer Extraction
- Move all draw_* methods to `BattleRenderer`
- Keep text caching with renderer

### Phase 5: Cleanup
- Remove old monolithic code
- Fix field naming inconsistencies
- Add type hints throughout

## Risks

- **Dual-write period** in Phase 2 will have temporary duplication
- **No existing tests** - adding tests during refactor is recommended
- **Feature freeze** - no new battle features during refactor to reduce scope

## Success Criteria

- Old battle.py (~820 lines) replaced with ~100 line coordinator
- Model can process actions without any UI code
- States handle their own input only (no cross-cutting logic)
- Renderer draws based on model state only
- Adding a new battle state requires only new state class + model support

---

# Implementation Complete

## Files Created

```
game/battle/
├── __init__.py       (25 lines)  - Module exports
├── dataclasses.py    (127 lines) - Actor, Action, Spell, BattleEvent, SpellType, SpellTarget
├── engine.py         (46 lines)  - SpeedQueue, calc_damage
├── model.py          (341 lines) - BattleModel with combat logic
├── states.py         (227 lines) - State handlers: CommandState, SpellSelectState, TargetState, ExecuteState, FlashState, MessageState, VictoryState, DefeatState
└── renderer.py       (273 lines) - BattleRenderer with all draw methods

game/scenes/battle.py (331 lines) - Scene coordinator
```

## Changes Made

1. **Architecture**: Split into Model (combat logic), States (input), Renderer (drawing)
2. **Type Safety**: Dataclasses for Actor, Action, BattleEvent instead of dicts
3. **Field Naming**: Fixed `level` -> `lvl`, `xp` -> `exp`, `xp_next` -> `exp_next` in menu.py
4. **Message Queue**: Added death messages ("X is slain!") to event queue
5. **Timing**: Flash animation (4x0.15s), message display (1.5s)

## Notes

- Flash animation is simplified (instant transition to next action)
- Message timing: 1.5 seconds per message, or press Z to skip
- Battle field naming now consistent: `lvl`, `exp`, `exp_next`, `def_`