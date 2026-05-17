# final fantasy gameboy style game

## tech stack
- use python
- use python arcade https://api.arcade.academy/en/stable/
- sqlite for data

## game components
- overworld map
- dungeon map
- town/castle/etc map
- battle system
- menu system (inventory, character stats, save, etc)
- title screen (new game, load, options)

## Implementation Plan

### Core Architecture

**Resolution**: 240×160 (GB Color base), scaled 1x-4x with integer steps

**Project Structure**:
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
│       └── overworld.py
├── data/              # Game data (JSON)
├── assets/            # Sprite sheets
├── saves/            # Save games
└── plan/
    └── concept.md    # Game concept and design
