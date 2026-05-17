# Phase 2.1: Enemy Sprite Atlas System

## Overview

Add enemy sprites to the battle system using sprite sheets from Final Fantasy Legend 2.

## Assets

| Sheet | File | Dimensions |
|-------|------|-------------|
| Enemies | `Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Enemies & Bosses - Enemies.png` | 802×274 |
| Characters | `Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Characters - Characters.png` | 465×718 |

## Implementation Steps

### Step 1: Create Sprite Picker Tool

**File:** `tools/sprite_picker.py`

A Python script using arcade to view sprite sheets and pick sprite regions.

**Features:**
- Zoom (scroll wheel) - 1x to 20x+, centered on cursor
- Pan (click + drag middle mouse OR arrow keys)
- Click + drag to select sprite region
- Display x, y, w, h of current selection
- Save selection to JSON
- Load multiple sprite sheets, switch with Tab

**Controls:**
- Mouse wheel: Zoom in/out
- Middle-click drag: Pan
- Left-click drag: Define selection rectangle
- Enter: Save current selection to clipboard/file
- Tab: Switch between loaded sheets

### Step 2: Create SpriteAtlas Class

**File:** `game/sprites.py`

```python
class SpriteAtlas:
    def __init__(self):
        self.sheets = {}  # name -> arcade.Texture
        self.definitions = {}  # sprite_id -> {sheet, x, y, w, h}

    def load_sheet(self, name: str, path: str):
        """Load a sprite sheet by name"""

    def load_definitions(self, json_path: str):
        """Load sprite definitions from JSON"""

    def draw(self, sprite_id: str, x: float, y: float, scale: float):
        """Draw sprite by ID at position (centered)"""
```

### Step 3: Create Sprite Definitions

**File:** `data/sprites.json`

```json
{
  "sheets": {
    "enemies": "Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Enemies & Bosses - Enemies.png"
  },
  "sprites": {
    "goblin": {"sheet": "enemies", "x": 0, "y": 0, "w": 16, "h": 16},
    ...
  }
}
```

Use sprite picker to identify positions for enemies in `data/enemies.json`:
- goblin
- skeleton
- slime
- wolf
- imp
- mage

### Step 4: Update Battle Renderer

**File:** `game/battle/renderer.py`

In `draw_enemy_area()` method (lines 87-92):
- Replace `arcade.draw_lrbt_rectangle_filled` colored placeholder
- Use `sprite_atlas.draw(enemy.sprite_id, cx, cy, scale)`

Changes needed:
1. Import SpriteAtlas
2. Add sprite_atlas parameter to renderer or create instance
3. Map enemy names to sprite IDs (e.g., "goblin" -> "goblin")
4. Draw sprites instead of rectangles

## Backward Compatibility

If sprite not defined in `data/sprites.json`, fall back to colored rectangle.

## Testing

1. Run sprite picker tool, verify zoom/pan/selection works
2. Pick 2-3 enemy sprites, save to JSON
3. Run battle, verify sprites appear correctly
4. Pick remaining enemy sprites
5. Verify all enemies show correct sprites in battle