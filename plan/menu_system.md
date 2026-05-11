# Menu System

## Overview

The menu is accessed from the overworld by pressing X. It uses a hierarchical state machine with the following screens:

```
MAIN
├── STATUS
│   └── (character detail)
├── ITEMS
│   └── (target selection)
├── MAGIC
│   └── (spell selection)
├── EQUIP
│   └── (slot selection)
│       └── (item selection)
├── SAVE
└── LOAD
```

## Controls
- UP/DOWN: Navigate
- Z: Select / Confirm
- X: Back / Cancel

## Main Menu
- STATUS: View party members and HP, select for details
- ITEMS: Use consumable items
- MAGIC: Cast spells (per character)
- EQUIP: Change equipment slots
- SAVE: Save game to slot (5 slots)
- LOAD: Load game from slot (5 slots)

## Status Screen
Shows party list with name, level, and HP. Selecting a character shows:
- Name and level
- Experience / next level
- HP and MP current/max
- ATK, DEF, MAG stats
- Equipped weapon, armor, helm, shield
- Known spells

## Items Screen
Lists all items with quantity and description. Selecting a consumable opens target selection (choose party member). Item effects:
- heal: restores HP
- mana: restores MP
- revive: resurrects with HP
- restore_all: full HP/MP (Tent)
- full_restore: full everything (Elixir)
- cure_status: removes status effect

## Magic Screen
Shows characters who have spells. Selecting one shows their spell list with MP cost. Spells are defined in `data/spells.json` with power, type, and target info.

## Equip Screen
Select a character, then a slot (weapon/armor/helm/shield). Shows current item and allows switching. Equipment bonuses are calculated at load time.

## Save/Load
5 slots. Saves store: party, inventory, gold, map, position, play time, equipment pool. Stored in `saves/saves.db` via SQLite.

## Engine Integration
- `engine.party` - list of character dicts
- `engine.inventory` - list of {id, qty}
- `engine.gold` - integer
- `engine.current_map` - map ID
- `engine.player_x/y` - position
- `engine.play_time` - seconds elapsed
- `engine.equip_item_pool` - available equipment IDs