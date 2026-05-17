# Phase 3: Maps & Tiles (Session Handoff)

## Current State

User approved the tile mapping preview. Ready to implement tile system.

## What Exists

- `scripts/convert_maps.py` — converts old maps.json tile IDs → GID grids
- `data/maps_converted.json` — output with GID grids for each map
- `assets/preview_converted.png` — approved mapping visual
- `assets/extracted_hometown_tileset_rgb.png` — 10x9 grid, 160x144, 16x16 tiles (GID 1-90)

## Approved Tile Mapping

### Non-tree tiles (simple 1:1)
| Old ID | Name | GID |
|--------|------|-----|
| 0 | Grass | 3 (sky/clouds) |
| 1 | Water | 15 (solid gray) |
| 3 | Path | 66 (solid ground) |
| 4 | Floor | 5 (brick floor) |
| 5 | Wall | 7 (detailed wall) |
| 6 | Door | 16 (doorway) |
| 7 | Sand | 3 (same as grass) |
| 8 | Mountain | 8 (dark trim) |
| 9 | Bridge | 12 (vertical stone) |

### Tree expansion rules (old tile_id=2)
- Left border (col 0): ALL rows → GID 1
- Right border (col 14): ALL rows → GID 1
- Top border (row 0): ALL cols → GID 1
- Bottom border (row 9): corners GID 1, rest GID 9
- Interior trees: no tree above → GID 9 (canopy), tree above → GID 2 (trunk)
- Pass 2: below row-0 GID 1 (col 1-13) → GID 2; below each GID 9 → GID 2
- Side borders (col 0/14) protected from override

Also need dungeon_1 and town_1 maps converted.

## Next Steps (in order)

1. `game/tiles.py` — Tileset class
   - Load extracted_hometown_tileset_rgb.png
   - Slice 10x9 grid (row-major: GID 1=top-left, GID 10=top-right...)
   - `get_texture(gid)` returns arcade.Texture
   - Cache textures

2. `game/tilemap.py` — Tilemap renderer
   - Take GID grid + tileset
   - Draw each tile at position
   - Handle offset/centering

3. Update overworld_states.py
   - OverworldRenderer.draw() uses Tilemap + Tileset instead of colored rects
   - Keep player, NPC, exit drawing as-is
   - Use gid grid from maps_converted.json (or load via new system)

4. Verify game runs (`python3 main.py`)

## File Structure Changes
```
game/
├── tiles.py       # NEW - Tileset loader
├── tilemap.py     # NEW - Tilemap renderer
└── scenes/
    └── overworld_states.py  # MODIFY - use tile system
data/
├── maps.json      # EXISTING - keep old format
└── maps_converted.json # EXISTING - GID grids
scripts/
└── convert_maps.py  # EXISTING - conversion tool
```
