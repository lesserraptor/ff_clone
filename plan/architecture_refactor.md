# Architecture Refactoring Plan

## Completed Steps

### Step 1 — PartyMember Dataclass (done)
Replaced `list[dict]` party data with typed `PartyMember` dataclass.

**Files created/modified:**
- `game/dataclasses.py` (NEW) — `PartyMember` dataclass with `to_dict()`, `from_dict()`, `take_damage()`, `heal()`
- `game/engine.py` — `party` is now `list[PartyMember]`, `calc_party_stats()` uses `base_atk`/`base_def`
- `game/scenes/menu.py` — all `member["hp"]` → `member.hp` etc.
- `game/scenes/battle.py` — party extraction uses `.name`, `.hp` etc.
- `game/battle/model.py` — removed duplicate `actor_to_dict()`

**Key fix:** `calc_party_stats()` no longer double-adds equipment on save/load. Uses `base_atk`/`base_def` fields stored separately from computed `atk`/`def_`.

**Save compat:** `PartyMember.from_dict()` falls back to legacy keys (`atk`→`base_atk`, `level`→`lvl`, `xp`→`exp`).

---

### Step 2 — Menu State Pattern (done)
Extracted 15-sub-state if/elif monolith into state classes.

**Files created/modified:**
- `game/scenes/menu_states.py` (NEW) — 10 state classes (492 lines)
- `game/scenes/menu.py` — thin coordinator (99 lines, was 512)

**State classes:** `MainMenuState`, `StatusMenuState`, `StatusCharMenuState`, `ItemsMenuState`, `ItemsUseMenuState`, `MagicMenuState`, `EquipMenuState`, `EquipSlotMenuState`, `SaveMenuState`, `LoadMenuState`

**Bug fixed:** Old `"magic_select"` state had no update handler, making spell selection broken. `MagicMenuState` now uses 2-phase internal state (`select_caster` / `select_spell`).

---

### Step 3 — pytest for Battle Model (done)
Added 46 tests covering the battle system.

**Files created:**
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_calc_damage.py` (6 tests)
- `tests/test_speed_queue.py` (6 tests)
- `tests/test_party_member.py` (11 tests)
- `tests/test_battle_model.py` (23 tests)

**Run with:** `.venv/bin/python -m pytest tests/ -v`

---

### Step 4 — Module-Level Init Cleanup (done)

**Problem:** Three import-time side effects: `load_game_data()` and `_register_font_early()` in `engine.py`, `init_db()` in `save.py`.

**Files modified:**
- `game/engine.py` — removed `_register_font_early()` function + call (Onion Pixel is the only font now), removed `load_game_data()` call from bottom
- `game/save.py` — removed `init_db()` call from bottom
- `game/__init__.py` — added `init_game()` function that calls `load_game_data()` + `init_db()`
- `main.py` — added `from game import init_game` + `init_game()` call before `GameWindow()` creation
- `tests/conftest.py` — calls `init_game()` before test collection
- `game/scenes/battle.py` — changed `from game.engine import SPELL_DATA` to lazy `import game.engine; self.spells = game.engine.SPELL_DATA` to avoid import-time reference capture

**Verification:** 46/46 tests pass. Import sanity check passes.

---

### Step 5 — OverworldScene Model/Renderer Split (done)
Split 308-line `OverworldScene` into model + renderer following battle module pattern.

**Files created/modified:**
- `game/scenes/overworld_states.py` (NEW) — `OverworldModel` + `OverworldRenderer`
  - `OverworldModel`: tile-based state + logic, no arcade deps. `update(dt, inpt)` returns events (`"battle"`, `"menu"`, `"exit"`). Uses `move_progress` (0.0→1.0) instead of pixel coords for smooth movement.
  - `OverworldRenderer`: all drawing (tiles, exits, NPCs, player, map name, dialog). Computes pixel positions from model tile pos + `move_progress` lerp.
  - Module-level `load_maps()`/`load_enemies()` moved here from old overworld.py.
- `game/scenes/overworld.py` — thin coordinator (43 lines, was 308). `update()` calls `model.update()`, syncs engine state, handles events. `draw()` delegates to renderer.

**Key design choices:**
- Model has no `engine` ref after `__init__` (reads initial state only)
- Events bridge model → coordinator: coordinator calls `engine.set_scene()` / syncs `engine.player_x/y`
- Player pixel position computed in renderer via: `center + (tile_pos - 7) * tile_size + lerp * move_progress`
- All behavior preserved: cooldown 0.15s, facing set on key press always, NPC check direction, battle chance 10%, dialog arrow indicator

**Verification:** 46/46 tests pass. Import sanity check passes. Game launches clean.

---

### Step 6 — Thinner Battle Coordinator (done)
Replaced 15-branch if/elif chain with dispatch dict + handler methods. Consolidated duplicate state checking in `draw()`.

**Files modified:**
- `game/scenes/battle.py` — `_handle_result()` refactored to `RESULT_DISPATCH` dict + 15 handler methods, extracted `_build_render_params()` for render param consolidation, cleaned up `draw()` (~320→270 lines)

**Key design:**
- `RESULT_DISPATCH` maps 13 result strings to handler method names
- Prefix-based fallback for `"message:"` and `"spell_target:"` results
- `_build_render_params()` replaces two redundant extraction blocks in `draw()` with single state-string-based pass

**Verification:** 46/46 tests pass.

---

### Step 7 — Low Priority Cleanups (done)
Three cleanup tasks: input import consistency, font dedup verification, pyglet key dependency removal.

**Files modified:**
- `game/input.py` — Removed 12 constant re-exports (`UP`, `DOWN`, `LEFT`, `RIGHT`, `ENTER`, `ESCAPE`, `Z`, `X`, `A`, `S`, `MINUS`, `EQUAL`). `update()` uses `pyglet_key.UP` etc. directly. Now exports only `InputState`.
- `game/battle/states.py` — Added `from pyglet.window import key` at top-level; removed 6 inline `from game.input import ...` from method bodies; replaced all key refs with `key.` prefix.
- `game/scenes/battle.py` — Changed import to `from pyglet.window import key`; replaced `Z` → `key.Z` (2 places in victory/defeat handlers).
- `game/scenes/title.py` — Changed import; replaced `UP`/`DOWN`/`Z` → `key.` prefix.
- `game/scenes/menu.py` — Changed import only (constants were unused imports).
- `game/scenes/menu_states.py` — Changed import; replaced `UP`/`DOWN`/`Z`/`X` → `key.` prefix in all state `update()` methods.
- `game/scenes/overworld_states.py` — Changed import; replaced all key refs with `key.` prefix.

**Key design:**
- `game.input` no longer re-exports pyglet key constants — modules import directly from `pyglet.window import key`.
- Font dedup verified: `_register_font_early()` was already removed in Step 4; `_register_font()` lives only in `text.py`.

**Verification:** 46/46 tests pass. Clean import check passes.

---

## Running Tests
```bash
cd /path/to/ff_clone
.venv/bin/python -m pytest tests/ -v
```

## Running the Game
```bash
cd /path/to/ff_clone
.venv/bin/python main.py
```

## Project Structure (current)
```
ff_clone/
├── main.py
├── game/
│   ├── __init__.py
│   ├── dataclasses.py          # PartyMember
│   ├── engine.py               # GameEngine, scene registry, game state
│   ├── input.py                # InputState
│   ├── save.py                 # SQLite save/load
│   ├── sprites.py              # Sprite atlas
│   ├── text.py                 # Font/text utilities
│   ├── ui.py                   # Drawing primitives
│   ├── battle/
│   │   ├── __init__.py
│   │   ├── dataclasses.py      # Actor, Action, Spell, BattleEvent
│   │   ├── engine.py           # SpeedQueue, calc_damage
│   │   ├── model.py            # BattleModel
│   │   ├── renderer.py         # BattleRenderer
│   │   └── states.py           # BattleState classes
│   └── scenes/
│       ├── __init__.py
│       ├── title.py
│       ├── overworld.py
│       ├── battle.py
│       ├── menu.py             # Thin coordinator
│       └── menu_states.py      # 10 menu state classes
├── data/
│   ├── enemies.json
│   ├── items.json
│   ├── maps.json
│   ├── spells.json
│   ├── sprites.json
│   └── ui_borders.json
├── assets/
├── saves/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_calc_damage.py
│   ├── test_speed_queue.py
│   ├── test_party_member.py
│   └── test_battle_model.py
└── plan/
    ├── phases.md
    ├── battle_system.md
    └── architecture_refactor.md    # THIS FILE
```
