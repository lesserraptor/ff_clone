# FF Clone — Architecture Document

> **GBC-style RPG using Python + arcade.** Base resolution 240×160,
> integer-scaled 1×–5× (default 3×). Source of truth is the code in
> `game/`, `data/`, `assets/`, `tests/`, `tools/`, and `scripts/`.
> This document describes what exists, not what to build.

---

## 1. Project Overview

FF Clone is a turn-based RPG in the style of Game Boy Final Fantasy
titles (1990s). It implements:

- **Title screen** with NEW GAME / LOAD GAME / OPTIONS
- **Overworld exploration** with tile-based movement, NPC dialog,
  exits between maps, and random battles
- **Turn-based battle system** with party commands, spells, items,
  enemy AI, level-ups, victory/defeat, death animations
- **Menu system** with sub-states for items, equip, status, and save
- **Save system** using SQLite with 5 slots
- **Sprite atlas** loading sprite sheets via JSON definitions,
  with background colour removal and mirror-of support

The game runs at a logical 240×160 resolution and is rendered at an
integer scale (default 3×) for crisp pixel-art appearance. All
`SpriteList.draw()` calls use `pixelated=True` to avoid blurring at
non-native scales.

---

## 2. Tech Stack

| Layer         | Technology                                       |
|---------------|--------------------------------------------------|
| Language      | Python 3.12+                                     |
| Game library  | `arcade` (built on pyglet / OpenGL)              |
| Map parser    | `pytiled_parser` — parses Tiled .tmx/.tsj files  |
| Image I/O     | `PIL` (Pillow) — sprite cropping, background removal, tile slicing |
| Font          | `pyglet.font` — registers Onion Pixel OTF before window creation |
| Persistence   | `sqlite3` — 5-slot save system                   |
| Testing       | `pytest` — 5 test files, 54 tests                |
| Data format   | JSON + Tiled .tmx/.tsj — enemies, items, spells, sprites, tile_defs & scripts (JSON), map grids / NPCs / exits (.tmx) |

There is no `pyproject.toml`; dependencies are managed via the
project's `.venv`.

---

## 3. Architecture

### 3.1 Scene State Machine

The game uses a **state-machine pattern** where each screen is a
"scene". Exactly one scene is active at any time, and scene
transitions are gated by a 2-frame `_scene_cooldown` to prevent
input bleed-through.

```
GameEngine (game/engine.py)
├── scene: object (current scene)
├── scene_name: str
├── set_scene(name) → looks up SCENES registry, constructs scene
└── update(dt) / draw() → delegates to current scene
```

All scenes are registered via the `@register_scene("name")`
decorator, which appends the class to the `SCENES` dict in
`game/engine.py`.

**Registered scenes:**
- `"title"` → `TitleScene` (`game/scenes/title.py`)
- `"overworld"` → `OverworldScene` (`game/scenes/overworld.py`)
- `"battle"` → `BattleScene` (`game/scenes/battle.py`)
- `"menu"` → `MenuScene` (`game/scenes/menu.py`)

### 3.2 GameEngine

`GameEngine` (`game/engine.py`) is the central state holder. It owns:

- `party: list[PartyMember]`
- `inventory: list[dict]` — each has `id` and `qty`
- `gold: int`
- `current_map: str`, `player_x`, `player_y`
- `play_time: float`
- `input: InputState`
- `window: arcade.Window` reference
- `equip_item_pool: list`

**Key methods:**
- `new_game()` — creates the default party of 4 (Warrior, Wizard,
  Rogue, Healer) with starting inventory and calls `calc_party_stats()`
- `get_state()` / `load_state(state)` — serialisation for saves
- `set_scene(name)` — transitions with cooldown
- `add_item(item_id, qty)` / `remove_item(item_id, qty)` /
  `has_item(item_id)` — inventory management

### 3.3 InputState

`InputState` (`game/input.py`) tracks keyboard state using pyglet
key constants. It maintains three sets:

- `keys_pressed`: currently held
- `keys_just_pressed`: pressed this frame (edge-triggered)
- `keys_just_released`: released this frame

It reads from `window.pressed_keys` (a `set` maintained by
`GameWindow.on_key_press/release`). `reset_frame_state()` clears
the just-pressed/just-released sets — called on scene transitions.

All scene code imports key constants from `pyglet.window import key`.

### 3.4 Module Split Pattern

Each major scene follows a **thin coordinator + model + renderer**
pattern:

```
OverworldScene (thin coordinator)
├── OverworldModel — pure state & logic, no arcade imports
└── OverworldRenderer — all drawing, caches text objects and tilesets

BattleScene (thin coordinator)
├── BattleModel — combat state & logic
├── BattleRenderer — all battle drawing
└── States (PartyCommandState, MessageState, etc.) — per-phase logic

MenuScene (thin coordinator)
└── 6 state classes in menu_states.py — per-screen logic & drawing
```

---

## 4. Directory Structure

```
ff_clone/
├── main.py                    # Entry point: GameWindow, on_update/on_draw
├── AGENTS.md                  # Agent instructions
├── plan/
│   ├── ARCHITECTURE.md        ← THIS FILE — single source of truth
│   └── (9+ old plan files, now superseded by ARCHITECTURE.md)
│
├── game/
│   ├── __init__.py            # init_game() — calls load_game_data() + init_db()
│   ├── engine.py              # GameEngine, register_scene, SCENES dict,
│   │                          #   calc_party_stats, load_game_data,
│   │                          #   DEFAULT_PARTY, ITEM_DATA, SPELL_DATA,
│   │                          #   WEAPON_DATA, ARMOR_DATA
│   ├── dataclasses.py         # PartyMember dataclass (from_dict/to_dict)
│   ├── input.py               # InputState — tracks keys held / just-pressed
│   ├── text.py                # Font registration, create_text, draw_text,
│   │                          #   wrap_text (Onion Pixel OTF)
│   ├── ui.py                  # draw_window, draw_cursor, draw_hp_bar,
│   │                          #   draw_mp_bar, draw_pixellated_border,
│   │                          #   draw_bordered_box, COLORS dict
│   ├── sprites.py             # SpriteAtlas (singleton) — loads sprite
│   │                          #   sheets + JSON definitions
│   ├── save.py                # SQLite save/load — 5 slots
│   ├── tiles.py               # Tileset — slices PNG into 16×16 GID textures
│   ├── tilemap.py             # Tilemap — renders GID grid with Y-flip
│   ├── tiled_map_loader.py    # Loads .tmx files via pytiled_parser,
│   │                          #   returns compat dict (gids, npcs, exits)
│   │
│   ├── scenes/
│   │   ├── __init__.py        # empty
│   │   ├── title.py           # TitleScene — NEW GAME / LOAD / OPTIONS
│   │   ├── overworld.py       # OverworldScene — thin coordinator
│   │   ├── overworld_states.py# OverworldModel + OverworldRenderer
│   │   ├── battle.py          # BattleScene — coordinator + dispatch
│   │   ├── menu.py            # MenuScene — coordinator + text cache
│   │   └── menu_states.py     # 6 menu state classes
│   │
│   └── battle/
│       ├── __init__.py        # Re-exports all battle types
│       ├── dataclasses.py     # Actor, Action, ActionType, BattleEvent,
│       │                      #   Spell, SpellType, SpellTarget,
│       │                      #   actor_from_dict, actor_to_dict
│       ├── engine.py          # SpeedQueue, calc_damage, create_action
│       ├── model.py           # BattleModel — combat logic, enemy AI,
│       │                      #   action queueing & execution
│       ├── states.py          # 11 battle state classes
│       └── renderer.py        # BattleRenderer — all battle drawing
│
├── data/
│   ├── enemies.json           # Enemy stats + encounter tables per map
│   ├── items.json             # Items, weapons, armor definitions
│   ├── spells.json            # Spell definitions + spell levels
│   ├── sprites.json           # Sprite sheet definitions + crop rects
│   ├── maps.json              # Tile IDs, tile defs, maps, exits, NPCs, scripts
│   ├── maps_converted.json    # maps.json with GID grids added by
│   │                          #   convert_maps.py
│   └── ui_borders.json        # 3×3 pixel border patterns for draw_pixellated_border
│
├── assets/
│   ├── onion-pixel.otf        # Primary game font
│   ├── onion-pixel.ttf        # TTF fallback
│   ├── *_tileset*.png         # Tileset spritesheets
│   ├── hometown_tileset.tsj  # Tiled JSON tileset — 10×9 grid of 16×16 tiles
│   │                          #   references extracted_hometown_tileset_rgb.png
│   ├── maps/                  # 5 .tmx map files (overworld_1/2/3, town_1,
│   │                          #   dungeon_1)
│   ├── Game Boy _ GBC - ... - Characters.png  # Character sprite sheet
│   ├── Game Boy _ GBC - ... - Enemies.png     # Enemy sprite sheet
│   └── Game Boy _ GBC - ... - Hometown.png    # Background reference
│
├── saves/                     # SQLite DB (saves.db) created at runtime
│
├── tests/
│   ├── conftest.py            # Adds project root to sys.path, calls init_game()
│   ├── test_calc_damage.py    # 6 tests — damage formula edge cases
│   ├── test_party_member.py   # 11 tests — PartyMember creation, damage,
│   │                          #   heal, serialisation, legacy fallback
│   ├── test_speed_queue.py    # 7 tests — ordering, insertion, empty
│   ├── test_battle_model.py   # 22 tests — model creation, actions,
│   │                          #   magic, victory/defeat, death, level-ups
│   └── test_tile_map.py       # 8 tests — Tiled map file existence, loading,
│                              #   GID grid, NPCs, exits, error handling,
│                              #   overworld model integration, gid_to_tile_id
│
├── tools/
│   ├── sprite_picker.py       # Interactive sprite region selector
│   ├── export_frames.py       # Export sprite frames as individual PNGs
│   ├── split_char_frames.py   # Split _all sprite rows into individual frames
│   └── convert_to_tiled.py    # Converts maps_converted.json → .tmx + .tsj
│                              #   CSV tile layers, object layers for NPCs/exits
│
└── scripts/
    └── convert_maps.py        # Tile-ID to GID converter + PNG preview
```

---

## 5. Major Units

### 5.1 Title Screen

`game/scenes/title.py` — `TitleScene`

The title screen displays "FINAL FANTASY" and three options: NEW
GAME, LOAD GAME, OPTIONS. A flashing cursor (> selector) animates
alongside the selected option text.

- **NEW GAME** (selection 0): calls `engine.new_game()` then
  `engine.set_scene("overworld")`
- **LOAD GAME** (selection 1): checks `has_save(0)` and if found,
  loads from slot 0 and transitions to overworld
- **OPTIONS** (selection 2): currently a no-op (placeholder)

Text is cached per-scale in `_texts` dict using `_get_text()` to
avoid recreating arcade.Text objects every frame.

### 5.2 Overworld System

`game/scenes/overworld.py` + `game/scenes/overworld_states.py`

Split into two classes:

**OverworldModel** — pure state and logic:

- Dual-source map loading via `load_maps()`:
  - Tile definitions (`tile_defs`), dialog scripts, and original logical
    tile grids come from `data/maps.json`
  - GID grids, NPCs, and exits come from `.tmx` files in `assets/maps/`,
    parsed via `game/tiled_map_loader.load_tiled_map()` using
    `pytiled_parser`
  - The two sources are merged per map: logical `tiles` from `maps.json`
    override the lossy GID→tile_id reverse mapping from the .tmx data
- Tile-based movement with **0.15-second move cooldown** to prevent
  tile-hopping
- Walk animation: 2-frame cycle (`walk_frame` 0 or 1) based on
  `move_progress`
- NPC dialog system: pressing Z facing an NPC triggers a dialog
  sequence from the `scripts` section of the map data
- **Random battles**: 10% chance per tile step via
  `random.random() < 0.1`, returns `{"type": "battle"}` event
- Exit system: tiles marked in `map_data["exits"]` trigger map
  transitions (dest_map / dest_x / dest_y)
- The player sprite ID follows the format defined in `sprites.json`
  with direction/frame keys (e.g. `warrior_dn_0`). The actual sprite
  ID construction is done via the `FACING_MAP` dict.

**OverworldRenderer** — all drawing:

- Caches text objects per scale
- Creates `Tileset` and `Tilemap` instances and caches them per
  map ID
- Renders: background, tilemap, exit outlines (yellow/transparent),
  NPC rectangles (red), non-walkable tile outlines, player sprite,
  map name label, NPC dialog box with arrow indicator

**OverworldScene** (coordinator):

- Owns model + renderer
- Syncs engine state (`player_x`, `player_y`) from model on each
  update so scene switches preserve position
- Handles events: battle, menu (X key), exit transitions

### 5.3 Battle System

Located in `game/battle/` as a self-contained sub-module.

#### Flow

The battle scene uses a string-based **state machine** with a
`RESULT_DISPATCH` dict mapping result strings to handler methods.
States flow:

```
party_command → char_command → target_enemy_attack / spell_select / item_select
              → run_attempt → run_outcome (→ escape / escape_failed)
                              → execute → flash → message → next_action
                                                           → next_round / victory / defeat
```

Each state is a class implementing `BattleState` (abstract base)
with `update(model, input_state, delta_time) → str | None` and
`get_message(model) → str`.

#### RESULT_DISPATCH

The `RESULT_DISPATCH` dict in `BattleScene` maps result strings to
handler method names. Additionally, prefix-based fallback handles:

- `"message:..."` → creates MessageState with the given text
- `"spell_target:..."` → routes to `_handle_spell_target` with
  spell ID
- `"item_target:..."` → routes to `_handle_item_target` with item ID

#### Key Components

| File | Contents |
|------|----------|
| `dataclasses.py` | `Actor`, `Action`, `ActionType` enum, `BattleEvent`, `Spell`, `SpellType` enum, `SpellTarget` enum, `actor_from_dict`/`actor_to_dict` |
| `engine.py` | `SpeedQueue` (priority queue by speed), `calc_damage(atk, def_)` |
| `model.py` | `BattleModel` — party/enemy init, action queueing, `prepare_battle()`, `execute_action()`, `check_battle_end()`, `apply_level_ups()` |
| `states.py` | `PartyCommandState`, `CharCommandState`, `SpellSelectState`, `TargetState`, `ItemSelectState`, `RunOutcomeState`, `ExecuteState`, `FlashState`, `MessageState`, `VictoryState`, `DefeatState` |
| `renderer.py` | `BattleRenderer` — draws backgrounds, enemy sprites, party info, menus, messages, flash overlay, death animations |
| `battle.py` | `BattleScene` — coordinator tying states + model + renderer together |

#### Damage Formula

```
damage = max(1, attacker.atk - target.def_)
```

This applies to both physical attacks and attack spells. For spells,
the spell's `power` replaces `attacker.atk`.

#### SpeedQueue

A `SpeedQueue` sorts actions by `actor.spd` descending. Actions for
all participants (party + enemies) are queued together and executed
in speed order each round. When speeds are equal, Python's stable
sort preserves insertion order (party actions first, then enemies).

#### Death and Animation

- Death is deferred via the `apply_death` field on `BattleEvent`.
  The actual `alive = False` assignment happens when the player
  advances past the death message in `MessageState.update()`.
- Enemies have a `dying_timer` set to 0.5s on death. The
  `_draw_death_animation` renders a two-phase collapse:
  - Phase 1 (0–70%): vertical shrink to 2px
  - Phase 2 (70–100%): horizontal shrink to 0px

#### Target Retargeting

If an action's target dies before the action executes (e.g. from
a faster ally's attack), `process_next_action()` auto-retargets to
the first living member of the same team.

#### Level-Ups

Level-ups grant: +5 `hp_max`, +2 `atk`, +1 `def_`, full HP restore,
`exp_next` multiplied by 1.5.

#### Victory Application

`_apply_victory()` grants EXP and gold to the party, levels up
surviving members, and converts `model.party` (list of `Actor`)
back to `engine.party` (list of `PartyMember`) via `actor_to_dict`
→ `PartyMember.from_dict`.

#### SPELL_DATA Lazy Import

`battle.py` uses:
```python
import game.engine; self.spells = game.engine.SPELL_DATA
```
rather than `from game.engine import SPELL_DATA`. This avoids
import-time reference capture, ensuring the data is populated after
`load_game_data()` has been called.

### 5.4 Menu System

`game/scenes/menu.py` + `game/scenes/menu_states.py`

**MenuScene** is a thin coordinator with:

- `set_state(name, **kwargs)` — creates a state object from
  `_state_classes` dict
- `_get_text()` — cached text helper

**6 state classes** in `menu_states.py`, each inheriting from
`MenuState` (abstract base):

| State | Purpose |
|-------|---------|
| `MainMenuState` | 3-panel layout: left menu (Items/Equip/Status/Save), right party list with sprites + HP/MP, bottom-right gold bar |
| `ItemsMenuState` | Full-screen 2/3-width panel listing inventory. Z on consumable → inline overlay target selector (alive party members). Applies heal/mana/revive/restore_all/cure_status effects |
| `StatusMenuState` | 4 stacked horizontal panels, each showing sprite + name + LV + HP/MP + ATK/DEF/MAG/SPD. X to go back |
| `EquipCharSelectState` | Party list with cursor. Z selects character → EquipDetailState. X to main |
| `EquipDetailState` | 4 layered panels: (1) stats bottom-left with preview arrows, (2) char ID top-left, (3) filtered equipment list right-full, (4) equipped slots right-bottom. Two-phase: navigate 5 slots (Weapon/Armor/Helm/Shield/Accessory) → Z → navigate filtered items with stat preview → Z equip. Slot selection preserved on back-nav |
| `SaveMenuState` | 3 full-width slot panels with border highlight selection. SQLite save via `game.save.save_game()`. DB query cached to avoid calling `init_db()` every frame |

All states use GBC-style panel layouts via `draw_window()` from `game.ui`,
matching the battle system's look-and-feel (`COLORS["box_fill"]` background,
`draw_pixellated_border` outlines).

**Removed states** (from the old 10-state system):
- `StatusMenuState` (old — party list → detail drill-down) → replaced by stacked panel layout
- `StatusCharMenuState` — no longer needed
- `ItemsUseMenuState` — inline target overlay in ItemsMenuState instead
- `MagicMenuState` — removed (magic handled in battle only)
- `EquipMenuState` (old) + `EquipSlotMenuState` — replaced by EquipCharSelectState + EquipDetailState
- `LoadMenuState` — removed (load from title screen only)

### 5.5 Save System

`game/save.py` — SQLite-based, stores saves in `saves/saves.db`.

**Schema:**
```sql
CREATE TABLE IF NOT EXISTS saves (
    slot INTEGER PRIMARY KEY,
    name TEXT,
    game_state TEXT,    -- JSON-serialized engine state
    timestamp TEXT,     -- ISO datetime
    play_time INTEGER
);
```

**API:**
- `init_db()` — called once at startup via `init_game()`
- `save_game(slot, name, game_state, play_time)`
- `load_game(slot)` → dict or None
- `delete_save(slot)`
- `get_all_saves()` → list of dicts
- `has_save(slot)` → bool

The stored `game_state` dict is the output of `engine.get_state()`,
which includes: party, inventory, gold, current_map, player_x/y,
play_time, equip_pool.

---

## 6. Data Layer

All data files live in `data/` as JSON.

### 6.1 enemies.json

```json
{
  "enemies": {
    "goblin": {"name": "Goblin", "hp": 20, "atk": 5, "def": 2, "spd": 6, "xp": 10, "gold": 5},
    ...
  },
  "encounters": {
    "overworld_1": ["goblin", "slime", "wolf"],
    ...
  }
}
```

Each map has an encounter list. If a map is not listed, a fallback
picks from all available enemies. Each battle spawns 1–2 random
enemies from that list.

### 6.2 items.json

Three sections: `items` (consumables), `weapons`, `armor`.

**Consumables:** Has `effect` (heal, revive, mana, restore_all,
full_restore, cure_status) and `value`.

**Weapons:** Have `atk` and optionally `mag` for magical weapons.

**Armor:** Have `def` and optionally `mag`. Sub-types include
armor, shield, helm — distinguished by `type`.
Accessories can also provide `atk` bonus (e.g. power_ring ATK+5, protect_ring DEF+5).

### 6.3 spells.json

Spells with `mp_cost`, `type` (attack/heal/revive/cure_status/
buff/debuff), `power`, `target` (enemy/ally). Mirror section
`spell_levels` groups spells by tier.

### 6.4 sprites.json

Defines sprite sheets and sprite crop rectangles:

```json
{
  "sheets": {"enemies": "Enemies.png", "characters": "Characters.png"},
  "sprites": {
    "goblin": {"sheet": "enemies", "x": 124, "y": 117, "w": 49, "h": 48},
    "warrior_dn_0": {"sheet": "characters", "x": 2, "y": 2, "w": 16, "h": 16},
    "warrior_lf_0": {"sheet": "characters", "mirror_of": "warrior_rt_0"},
    ...
  }
}
```

Entries with `mirror_of` are horizontal flips of another sprite,
generated at load time.

### 6.5 Maps

Maps use a **dual-format** system. Static metadata lives in JSON
while spatial data (grids, objects) lives in Tiled .tmx files.

**`data/maps.json`** contains:

- `tile_defs` — maps tile IDs to `walkable`, `name`, `color`
- `maps` — each with `id`, `name`, `width`, `height`,
  `tiles` (2D int grid), `npcs`, `exits`, `scripts`
- `scripts` — dialog arrays keyed by script ID

**`data/maps_converted.json`** is the output of `convert_maps.py` —
identical to `maps.json` but with an additional `gids` grid per map
(GID numbers for the pixel tileset). Overworld maps get tree-expansion
logic; non-overworld maps get a simple 1:1 ID→GID mapping.

**`assets/maps/*.tmx`** — Tiled XML map files (5 total:
`overworld_1`, `overworld_2`, `overworld_3`, `town_1`, `dungeon_1`).
Each contains:
- A **CSV-encoded tile layer** with GID values
- An **NPCs object layer** — point objects with custom properties
  (`name`, `script_id`)
- An **Exits object layer** — point objects with custom properties
  (`dest_map`, `dest_x`, `dest_y`, `direction`)

**`assets/hometown_tileset.tsj`** — Tiled JSON tileset definition.
References `assets/extracted_hometown_tileset_rgb.png` with a 10×9
grid of 16×16 tiles (90 tiles total). Each tile has a `walkable`
boolean custom property. Generated by `tools/convert_to_tiled.py`.

**Loading pipeline** (`game/scenes/overworld_states.py:load_maps()`):
1. Load `tile_defs` and `scripts` from `data/maps.json`
2. For each `.tmx` in `assets/maps/`, call
   `game/tiled_map_loader.load_tiled_map()` to get GID grid, NPCs,
   exits
3. Merge: logical `tiles` grid from `maps.json` overrides the
   lossy GID→tile_id reverse mapping (tree expansion in GIDs
   cannot be reversed perfectly)

### 6.6 ui_borders.json

Defines the 3×3 pixel-letter grid for `draw_pixellated_border()`:

- `top_left` / `top_right` / `bot_left` / `bot_right` — corner
  patterns (6×6 grid of `w`/`g`/`b`/`t` characters)
- `top_border` / `bot_border` — horizontal edge rows
- `left_edge` / `right_edge` — vertical edge strips
- `colors` — letter→colour mapping: `w`=light, `g`=mid, `b`=dark,
  `t`=transparent

Border colours are derived from the user-supplied `border_color`
by lightening (`w`) and darkening (`b`) the RGB values.

---

## 7. Sprite System

**`game/sprites.py`** — `SpriteAtlas` singleton class.

### Loading

1. `load_definitions(json_path)` reads `sprites.json` to get
   `sheets` (filename per sheet name) and `sprites` (definitions).
2. Each sheet file is loaded as an `arcade.Texture`.
3. **Background colour detection**: Reads the four corner pixels of
   each full sheet to detect the dominant background colour. This
   colour is then set to transparent in individual sprite crops.
4. **First pass** (crops): For each sprite definition with x/y/w/h
   coordinates, the region is cropped from the sheet texture, the
   background colour is removed (pixels matching the detected colour
   have their alpha set to 0), and the result is saved to a
   `BytesIO` buffer as PNG, then loaded via `arcade.load_texture(buf)`.
5. **Second pass** (mirrors): Entries with `mirror_of` are created
   by flipping the source texture horizontally (via PIL
   `Image.transpose(FLIP_LEFT_RIGHT)`) and loading through BytesIO.

### PIL BytesIO Workaround

Arcade's `Texture.crop()` method has a bug when cropping from the
same sheet multiple times: `"texture not found in UVData"`. The
workaround is to crop using PIL, save to a `BytesIO` buffer, and
load that buffer with `arcade.load_texture(buf)`.

### Drawing

`atlas.draw(sprite_id, x, y, scale)` creates a one-shot
`arcade.SpriteList` with a single sprite, sets the texture, and
calls `draw(pixelated=True)`.

---

## 8. UI System

**`game/ui.py`** — Drawing primitives using arcade.

### COLORS dict

```python
COLORS = {
    "box_fill": (232, 232, 232),
    "box_border": (160, 160, 160),
    "text": (24, 24, 24),
    "cursor": (24, 24, 24),
    "hp_fill": (48, 48, 48),
    "hp_empty": (160, 160, 160),
    "mp_fill": (80, 80, 80),
    "mp_empty": (160, 160, 160),
}
```

### draw_pixellated_border(x, y, w, h, scale, border_color)

Renders a 6-pixel (at scale) 3D-look border around a rectangle
using data-driven patterns from `ui_borders.json`. The border has
a pseudo-3D SNES-style appearance with light/mid/dark shades on
top/left vs bottom/right edges.

### draw_window(x, y, w, h, scale, fill_color, border_color)

Draws a filled rectangle with `draw_pixellated_border` around it.
The 6-pixel border width is subtracted from the interior fill.

### draw_cursor(x, y, scale, color)

Draws a right-pointing triangle (▶) cursor for menu selection. 8×8
pixels at scale.

### draw_hp_bar / draw_mp_bar

Draw a horizontal bar with empty background, filled portion, and
outline. Default size 40×4 pixels at scale.

### draw_bordered_box

Simple filled rectangle with outline (no pixel-art border).

---

## 9. Text System

**`game/text.py`** — Onion Pixel OTF font integration.

### Font Registration

The font file `assets/onion-pixel.otf` is registered with pyglet
via `pyglet.font.add_file()` **before** `arcade.Window()` is
created. This is critical — registering fonts after window creation
may not take effect.

`load_font()` returns the font name `"Onion Pixel"` (the
PostScript/OpenType family name).

### Functions

- `create_text(text, x, y, color, size, anchor_x, anchor_y, width,
  multiline)` → `arcade.Text` object (reusable, cached by callers)
- `draw_text(text, x, y, color, size, scale)` → immediate draw
  (not cached)
- `wrap_text(text, max_width, font_size, scale)` → list of strings
  wrapped at character-count boundaries (approx `font_size * 0.6`
  pixels per character)
- `get_text_width(text, size, scale)` → approximate width

### init_game() Pattern

`game/__init__.py` exports `init_game()` which calls:
1. `load_game_data()` — loads items, weapons, armor, spells into
   module-level dicts
2. `init_db()` — creates SQLite tables

Font registration happens inside `_register_font()` (called by
`load_font()`, which is called by every text operation). The
registration is guarded by a `_font_registered` flag.

---

## 10. Tests

5 test files, 54 tests total, using `pytest`.

### conftest.py

Adds project root to `sys.path` and calls `init_game()` to load
game data before any tests import game modules.

### test_calc_damage.py (6 tests)

Tests `calc_damage()`: atk > def, atk == def (minimum 1), atk < def,
zero values, high values, both zero.

### test_party_member.py (11 tests)

Tests `PartyMember`: defaults, take_damage (non-lethal, lethal,
overkill), heal (normal, capped), is_alive, to_dict (computed fields
omitted), from_dict roundtrip, from_dict legacy field fallback
(`atk`/`def`/`level`/`xp`), mutable default list isolation.

### test_speed_queue.py (7 tests)

Tests `SpeedQueue`: empty, add one, pop returns highest speed first,
clear, len, same-speed insertion order.

### test_battle_model.py (22 tests)

Tests `BattleModel`: party/enemy creation, living lists, queue
actions (attack/magic), prepare_battle builds queue, process_next_action,
attack damage, enemy attack damage, minimum damage, attack spell,
heal spell, victory/defeat detection, both-dead edge case, kill
enemy triggers rewards, death message, level-ups (single, multiple,
stats increase).

### test_tile_map.py (8 tests)

Tests Tiled map loading and conversion:
- `.tmx` file existence for all maps in `maps_converted.json`
- Basic load: width, height, name, tile_size, id
- GID grid dimensions and value types
- NPC parsing (town_1 has King at (4, 2) with script `king_intro`)
- Exit parsing (overworld_1 exits to overworld_2 at (1, 5))
- `FileNotFoundError` on missing .tmx
- OverworldModel integration: `load_maps()` returns merged data from
  both .tmx and maps.json sources
- `gid_to_tile_id()` reverse mapping covers all used GIDs

---

## 11. Tools

### sprite_picker.py

Interactive GUI tool (`arcade.Window`) for selecting sprite regions
from sprite sheets. Features:

- Pan (middle-mouse drag), zoom (scroll wheel, 1/2/4/8× presets)
- Pixel grid overlay (G key, visible at ≥2× zoom)
- **Guided mode** (`--class warrior`): steps through 6 frame slots
  (dn_0, dn_1, rt_0, rt_1, up_0, up_1), saves each to
  `data/sprites.json`, then auto-generates mirrored left frames
- Manual queue mode: select region → Enter → name → queue
- S to save all queued to JSON
- Tab to switch between enemy and character sheets

### convert_maps.py

Converts `data/maps.json` tile IDs to GID (graphic ID) values for
`data/maps_converted.json`:

- Overworld maps: tree-expansion logic (canopy at top, trunk below,
  GID 1 border)
- Non-overworld maps: simple 1:1 ID→GID mapping via lookup table
- Generates a PNG preview of `overworld_1` using the tileset

### export_frames.py

Exports individual sprite frames from sprite sheets as standalone
PNGs. Reads `data/sprites.json`, crops or mirrors each entry, saves
to project root. Useful for asset inspection.

### split_char_frames.py

Splits `_all` entries in `sprites.json` (6-frame rows: 18px per
slot, 16px content + 2px padding) into individual frame entries
with proper names (`dn_0`, `dn_1`, `rt_0`, `rt_1`, `up_0`, `up_1`)
and auto-generates mirrored left frames (`lf_0`, `lf_1` via
`mirror_of`).

### convert_to_tiled.py

Converts `data/maps_converted.json` to Tiled .tmx and .tsj formats
for editing in the Tiled map editor.

- **Tileset output** (`assets/hometown_tileset.tsj`): JSON tileset with
  `walkable` bool custom property per tile (90 tiles, 10×9 16×16 grid)
- **Map output** (`assets/maps/<map_id>.tmx`): Tiled XML map per map
  with:
  - CSV-encoded tile layer (single-line comma-separated GIDs — required
    by `pytiled_parser` to avoid multi-line parse issues)
  - `NPCs` object layer: point objects with `name` and `script_id`
    custom properties
  - `Exits` object layer: point objects with `dest_map`, `dest_x`,
    `dest_y`, `direction` custom properties
- Regenerates all 5 maps from the converted JSON source

Run via `python3 tools/convert_to_tiled.py`.

---

## 12. Assets

Located in `assets/`:

| File / Directory | Purpose |
|------------------|---------|
| `onion-pixel.otf` | Primary game font (registered with pyglet) |
| `onion-pixel.ttf` | TTF variant of same font |
| `extracted_hometown_tileset.png` | Tileset (10×9 grid of 16×16 tiles) |
| `extracted_hometown_tileset_rgb.png` | RGB version of same tileset |
| `overworld_pixel_tileset.png` | Alternative overworld tileset |
| `overworld_placeholder_tileset.png` | Placeholder tileset |
| `hometown_tileset.tsj` | Tiled JSON tileset — 90 tiles, 10×9 grid, `walkable` per-tile property |
| `maps/` | 5 `.tmx` files: `overworld_1`, `overworld_2`, `overworld_3`, `town_1`, `dungeon_1` |
| `Game Boy _ GBC - ... - Characters.png` | Character sprite sheet |
| `Game Boy _ GBC - ... - Enemies.png` | Enemy sprite sheet |
| `Game Boy _ GBC - ... - Hometown.png` | Background reference image |

---

## 13. Key Errata & Gotchas

### Field Naming Consistency

All code uses:
- `lvl` not `level`
- `exp` not `xp`
- `exp_next` not `xp_next`
- `def_` (with underscore suffix) to avoid shadowing Python's
  `def` keyword

**`PartyMember.from_dict()`** has fallback for legacy keys:
- `d.get("lvl", d.get("level", 1))`
- `d.get("exp", d.get("xp", 0))`
- `d.get("exp_next", d.get("xp_next", 100))`
- `d.get("base_atk", d.get("atk", 10))`
- `d.get("base_def", d.get("def", 5))`

Legacy `PartyMember` fields `atk` and `def` were removed from
`to_dict()` — they are now computed fields overwritten by
`calc_party_stats()`.

### calc_party_stats() Double-Add Bug

The function stores `base_atk`/`base_def` separately from computed
`atk`/`def_`. This prevents equipment bonuses being applied
multiple times if `calc_party_stats()` is called more than once.
It is called on `new_game()` and `load_state()`.

### Font Registration Order

`pyglet.font.add_file()` must be called **before** `arcade.Window()`
is created. The flow in `main.py` is:

1. `init_game()` — calls `load_game_data()` + `init_db()`
2. `GameWindow()` — constructs window
3. `window.setup()` — creates GameEngine, imports scenes,
   sets initial scene

The font is registered lazily inside `_register_font()`, called by
`load_font()`, which is called the first time any text is rendered.

### init_game() Pattern

No import-time side effects. Modules export data; `init_game()`
explicitly calls `load_game_data()` + `init_db()`. This ensures
test files can import modules without triggering side effects.

### SPELL_DATA Lazy Import

`game/scenes/battle.py` uses:
```python
import game.engine; self.spells = game.engine.SPELL_DATA
```
instead of `from game.engine import SPELL_DATA`. The latter would
capture the module-level reference before `load_game_data()` has
populated it.

### Arcade Texture / UV Bug

Cropping from the same texture multiple times using
`arcade.Texture.crop()` causes `"texture not found in UVData"`.
Workaround: use PIL to crop → save to `BytesIO` → load with
`arcade.load_texture(buf)`.

### pixelated=True

Every `SpriteList.draw()` must use `pixelated=True` to maintain
crisp pixel-art appearance at integer scales. Arcade defaults to
bilinear filtering which blurs scaled pixel art.

### Scene Cooldown

`GameEngine._scene_cooldown = 2` frames after each scene transition.
During these frames, `input.update()` still runs but the scene's
`update()` will not process input from the previous scene.

### Move Cooldown

Overworld movement has a 0.15-second cooldown
(`_move_cooldown = 0.15`) to prevent the player from hopping
multiple tiles per keypress.

### Battle RESULT_DISPATCH Pattern

The `RESULT_DISPATCH` dict in `BattleScene` maps result strings to
handler method names. Prefix-based fallback handles:
- `"message:*"` → `_handle_message(text)`
- `"spell_target:*"` → `_handle_spell_target(spell_id)`
- `"item_target:*"` → `_handle_item_target(item_id)`

### Deferred Death

Battle death is applied via `apply_death` on `BattleEvent`. The
`alive = False` assignment happens when the player advances past
the death message in `MessageState`, not at the moment of damage.
This gives the message system time to display "X falls!" before the
character disappears.

### Enemy Death Animation

Enemies get `dying_timer = 0.5` on death. The renderer draws a
two-phase collapse:
1. Vertical shrink (top/bottom pull to center) over first 70% of
   timer
2. Horizontal shrink to 0px over remaining 30%

### Target Retargeting

`process_next_action()` auto-retargets dead targets to the first
living member of the same team. This prevents actions from being
lost when a fast character kills the intended target before the
slower attacker acts.

### Menu MagicMenuState 2-Phase Internals

`MagicMenuState` uses a `phase` field (`"select_caster"` /
`"select_spell"`) to manage two-level navigation within a single
state class. The old implementation had a non-functional
`"magic_select"` string state that lacked an update handler.

### SpellSelectState Cancel Routing

Pressing X in `SpellSelectState` returns `"char_command"` (not
`"command"`). The dispatch correctly routes this to
`_handle_char_command` which re-enters `CharCommandState`.

### InputState Key Tracking

`InputState` tracks only a whitelist of keys (arrow keys, Z, X,
Return, Escape, A, S, +, -). Other keys are ignored. This
whitelist is defined in `InputState.update()`.

### Event System for Stateful Scenes

The overworld model returns event dicts (battle, menu, exit) rather
than calling scene transitions directly. The thin coordinator
(`OverworldScene`) dispatches these events. This keeps the model
pure and reusable.

### Battle Victory → Engine Sync

On victory, `_apply_victory()` converts BattleModel's `Actor` list
back to engine PartyMember list via `actor_to_dict()` →
`PartyMember.from_dict()`. This two-step conversion ensures the
engine's party reflects combat outcomes (HP changes, level-ups,
death status).

### Tiled Y-Axis Convention Matches Y-Flip

Tiled uses a Cartesian Y-axis (row 0 = bottom). The overworld
renderer applies a Y-flip (`map_h - 1 - ty`) so that row 0 = top,
matching the tile grid convention used throughout the rest of the
codebase. The `load_tiled_map()` function reads raw tile
coordinates from Tiled object layers and converts them to the same
Y-flipped coordinate space as the GID grid.

### Dual-Source Map Load: tile_defs/Scripts vs Grid/NPC/Exits

`load_maps()` in `overworld_states.py` merges data from two
independent sources:

1. **`data/maps.json`** — provides `tile_defs` (walkability, names,
   colours), dialog `scripts`, and the original logical `tiles`
   grid
2. **`assets/maps/*.tmx`** — provides the visual `gids` grid for
   rendering, plus `npcs` and `exits` as object layers

The logical `tiles` grid from `maps.json` overrides the
GID→tile_id reverse mapping calculated inside
`tiled_map_loader.py`. This is necessary because the
`convert_maps.py` tree-expansion step collapses multiple GIDs into
a single logical tile ID, and the reverse mapping in
`_GID_TO_TILE_ID` cannot perfectly recover the pre-expansion IDs.
