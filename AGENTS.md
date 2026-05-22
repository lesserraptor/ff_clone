# FF Clone Agent Instructions

## IMPORTANT - Workflow
- verify with the user whether a spec can be accepted as done or not

## Project Overview
This is a Final Fantasy-style game in the style of the old Game Boy titles, using Python + arcade.

**Tech Stack**:
- Python with arcade library
- Base resolution: 240x160 (GBC), integer scaled 1x-4x
- JSON for map/enemy/item/spell data
- SQLite for save games (not yet implemented)

**File Structure**:
```
ff_clone/
├── main.py           # Entry point
├── game/
│   ├── __init__.py
│   ├── engine.py    # Scene state machine
│   ├── input.py    # Input handling
│   └── scenes/
│       ├── __init__.py
│       ├── title.py
│       ├── overworld.py
│       ├── battle.py    # Battle system
│       └── menu.py      # Menu system
├── data/
│   ├── enemies.json
│   ├── items.json
│   └── spells.json
├── assets/         # Sprite sheets
├── saves/          # (empty, for save games)
└── plan/
    └── battle_system.md  # Detailed battle docs
```

**Controls**:
- Arrow keys: Move / Navigate
- Z: Select/confirm
- X: Cancel/back
- +/-: Scale up/down

## Key Conventions

- Battle system uses `plan/battle_system.md` for detailed documentation
- Party members have: name, hp, hp_max, atk, def, spd, alive, level, xp, xp_next
- Battle states: party_command → party_target → flash → message → execute
- Use the venv to run `python3 main.py` to run (arcade must be installed)
- Sync any field name changes between battle.py and menu.py (e.g., level vs lvl)
