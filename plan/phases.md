# FF Clone Phases

## Phase 1 - Core Skeleton
- Window with scaling (1x-4x integer) ✅
- Basic scene state machine (title → overworld) ✅
- Input handling and screen transition ✅

**Status**: COMPLETE

---

## Phase 2 - Overworld
- Tile-based map renderer from JSON ✅
- Player sprite movement ✅
- 2-3 overworld screens with exits ✅
- 1 town map (tiles + NPC placeholder) ✅
- 1 small dungeon (2-3 rooms) ✅

**Status**: COMPLETE

---

## Phase 3 - Battle System
- Random encounter trigger from overworld ✅
- Turn-based battle UI ✅
- 4 blank party slots + basic commands (Fight, Magic, Item, Run) ✅
- Enemy data and damage calculations ✅

**Status**: COMPLETE

---

## Phase 4 - Menu & Save
- Main menu (status, inventory, magic, equip, save/load) ✅
- Save/load with SQLite ✅
- Full RPG menu with equipment slots ✅
- Scene transition fix (2-frame input cooldown) ✅

**Status**: COMPLETE

---

## Phase 5 - Architecture Refactoring

### Step 1 — PartyMember Dataclass ✅
- `game/dataclasses.py` — typed PartyMember replacing `list[dict]`
- Fixed `calc_party_stats()` double-add bug on save/load
- Save-compatible with legacy dict format

### Step 2 — Menu State Pattern ✅
- `game/scenes/menu_states.py` — 10 state classes
- `game/scenes/menu.py` — thin coordinator (99 lines, was 512)
- Fixed broken magic spell selection input

### Step 3 — pytest for Battle Model ✅
- 46 tests across 4 test files
- Covers: damage calc, SpeedQueue, PartyMember serialization, BattleModel combat logic

### Step 4 — Module-Level Init Cleanup ✅
- Removed `_register_font_early()` (Onion Pixel only), `load_game_data()`, `init_db()` from import time
- Added `init_game()` to `game/__init__.py` — called from `main.py` and `tests/conftest.py`
- Fixed `SPELL_DATA` lazy import in `battle.py` to avoid import-time reference capture

### Step 5 — OverworldScene Model/Renderer Split ✅
- `game/scenes/overworld_states.py` — `OverworldModel` + `OverworldRenderer`
- `game/scenes/overworld.py` — thin coordinator (43 lines, was 308)

### Step 6 — Thinner Battle Coordinator
- Clean up 336-line battle scene with dispatch dict

### Step 7 — Low Priority Cleanups
- Input import consistency, font dedup, etc.
