# Graphics Implementation Plan

## Overview

This document details the implementation of the graphics system for the FF Clone game, covering fonts, sprites, UI elements, and map tiles. The goal is to create a replaceable "skin" system where all graphics can be changed by swapping assets without modifying game code.

## Phase 1: Font + UI (partially completed)

### 1.1 Font System (completed)

**Purpose:** Replace arcade's default system font with a custom Final Fantasy font.

**Asset:**
- `assets/onion-pixel.otf` (replaced final-fantasy-iv-japan-only.ttf)

**Font name:** "Onion Pixel"
- TrueType font file with Final Fantasy IV characters
- Contains both Japanese and ASCII characters

**Implementation Notes (Important!):**

Arcade uses pyglet for text rendering. For custom fonts to work, they must be registered with pyglet BEFORE any arcade windows are created. This is a critical implementation detail:

```python
# In game/engine.py - executed at module load time, before any Window is created
import pyglet.font

def _register_font_early():
    import os
    font_path = os.path.join(os.path.dirname(__file__), "..", "assets", "final-fantasy-iv-japan-only.ttf")
    if os.path.exists(font_path):
        pyglet.font.add_file(font_path)

_register_font_early()
```

The font must be registered this way because:
1. Arcade creates a GL context when the Window is initialized
2. Pyglet needs to know about custom fonts before that context is created
3. Once registered, arcade.Text and arcade.draw_text will use the font by name

**API:**

Create `game/text.py`:
```python
import os
import pyglet.font

_font_registered = False

def _register_font():
    global _font_registered
    if _font_registered:
        return True
    
    font_path = os.path.join(_get_assets_path(), "final-fantasy-iv-japan-only.ttf")
    if os.path.exists(font_path):
        pyglet.font.add_file(font_path)
        _font_registered = True
        return True
    return False

def load_font():
    _register_font()
    return "Final Fantasy IV (Japan only)"  # The font's registered name

def create_text(text, x, y, color, size, anchor_x, anchor_y):
    return arcade.Text(text, x, y, color, size, font_name=load_font(), anchor_x=anchor_x, anchor_y=anchor_y)

def draw_text(text, x, y, color, size, scale, anchor_x, anchor_y):
    import arcade
    arcade.draw_text(text, x, y, color, int(size * scale), font_name=load_font(), anchor_x=anchor_x, anchor_y=anchor_y)
```

### 1.2 Battle Renderer Font Update (complete) 

**Purpose:** Update `game/battle/renderer.py` to use the custom font for all text rendering.

**Current State:**
The battle renderer currently uses `arcade.Text()` directly without specifying `font_name`, which means it falls back to system fonts.

**Required Changes:**

1. Replace direct `arcade.Text()` calls with `create_text()` from `game/text.py`:
   - Enemy HP/name text (line ~74)
   - Party member name/HP/MP text (lines ~95-113)
   - Command bar options (line ~127)
   - Spell list (lines ~157, ~171)
   - Message box text (lines ~251-255)
   - Instruction text (line ~270)

2. Update text caching pattern to match `title.py`:
   ```python
   def _get_text(self, key, text, size, color, anchor_x="center"):
       scale = self.engine.get_scale()
       if self._prev_scale != scale or key not in self._texts:
           self._texts[key] = create_text(text, 0, 0, color, size, anchor_x=anchor_x, anchor_y="center")
           self._prev_scale = scale
       return self._texts[key]
   ```

3. Update text positions in `draw()` loop:
   ```python
   text = self._get_text(key, text, font_size, color)
   text.x = x_pos
   text.y = y_pos
   text.draw()
   ```

### 1.3 UI System

**Purpose:** Create menu windows, cursors, and HP/MP bars matching FF Legend II style.

**Reference Image:**
- `assets/final-fantasy-legend-ii-screenshot-6_scale_800_700.jpg`

**Colors (from reference):**

| Element | RGB |
|--------|-----|
| Box fill | (48, 48, 160) - dark blue |
| Box border | (160, 160, 160) - light gray |
| Text | (255, 255, 255) - white |
| Cursor | (255, 255, 0) - yellow |
| Enemy HP/Name | (255, 48, 48) - red |
| Player HP/MP | (48, 112, 208) - blue |

**Implementation:**

Create `game/ui.py` with pixellated border following FF Legend II style:

```python
COLORS = {
    "box_fill": (48, 48, 160),
    "box_border": (160, 160, 160),
    "text": (255, 255, 255),
    "cursor": (255, 255, 0),
    "enemy": (255, 48, 48),
    "player_hp": (48, 112, 208),
    "hp_fill": (0, 200, 0),
    "mp_fill": (48, 48, 255),
}

def draw_window(x, y, w, h, scale, fill_color=None, border_color=None):
    """Draw blue box with pixellated 3D border"""

def draw_cursor(x, y, scale, color=None):
    """Draw yellow triangle cursor"""

def draw_hp_bar(current, max_val, x, y, scale, width=None, height=None):
    """Draw HP bar (green fill, border)"""

def draw_mp_bar(current, max_val, x, y, scale, width=None, height=None):
    """Draw MP bar (blue fill, border)"""
```

**Border Implementation Details:**

The border data is loaded from `data/ui_borders.json` at runtime, allowing style changes without code edits.

The JSON defines:
- **Corners:** 6x6 pixel patterns (top_left, top_right, bot_left, bot_right)
- **Top/bottom edges:** 6 rows of solid colors (top_border, bot_border)
- **Left/right edges:** 6-character strings (left_edge, right_edge)

Each character maps to: w=light, g=mid, b=dark, t=transparent.

See `plan/menu_border_desc.md` for the default pixel patterns and `data/ui_borders.json` for the actual data.

**Updated Renderers:**

1. `game/scenes/title.py` - Uses `create_text()` for all text
2. `game/scenes/menu.py` - Uses `draw_window()` and `COLORS`, cached text via `_get_text()`
3. `game/scenes/overworld.py` - Uses `draw_text()` and `draw_window()`, cached text via `_get_text()`
4. `game/battle/renderer.py` - Uses `draw_window()`, `COLORS`, colored HP/MP bars, cached text

**Text Caching Pattern:**

All scenes now use a consistent caching pattern to avoid `arcade.draw_text` PerformanceWarning:

```python
self._text_cache = {}  # keyed by scale, then by text key

def _get_text(self, key, text, x, y, color, size, anchor_x="left", anchor_y="center"):
    scale = self._prev_scale  # set at end of draw()
    if scale not in self._text_cache:
        self._text_cache[scale] = {}
    cache = self._text_cache[scale]
    if key not in cache:
        cache[key] = create_text(text, x, y, color, size, anchor_x=anchor_x, anchor_y=anchor_y)
    else:
        cache[key].text = text
        cache[key].color = color
        cache[key].x = x
        cache[key].y = y
    return cache[key]
```

---

## Phase 2: Sprites 

### 2.1 Sprite Atlas System

**Purpose:** Load and display sprite sheets with a data-driven approach.

**Key Learning:** Sprites have variable sizes (not fixed 16x16). Arcade's SpriteList has a texture atlas limitation requiring each sprite to be preloaded as an independent texture.

**Assets:**

| Asset | File | Size | Notes |
|-------|------|------|-------|
| Characters | `assets/Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Characters - Characters.png` | 465×718 | Multiple poses/directions |
| Enemies | `assets/Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Enemies & Bosses - Enemies.png` | 802×274 | Variable size sprites |

**Implementation:**

Create `tools/sprite_picker.py` - Interactive tool for picking sprite regions from sheets:
- Zoom (scroll wheel), Pan (middle-click drag or arrows)
- Left-click drag to select region
- Enter to save with name to JSON
- Tab to switch between loaded sheets

Create `game/sprites.py`:
```python
class SpriteAtlas:
    def __init__(self, assets_path=None):
        self.sheets = {}      # name -> arcade.Texture (full sheet)
        self.definitions = {} # sprite_id -> {sheet, x, y, w, h}
        self.sprite_textures = {} # sprite_id -> arcade.Texture (preloaded)

    def load_definitions(self, json_path):
        """Load sheet references and sprite definitions from JSON"""
        # Loads sheets, then preloads each sprite as independent texture
        # (workaround for arcade SpriteList atlas limitation)

    def draw(self, sprite_id, x, y, scale):
        """Draw sprite by ID using arcade.Sprite + SpriteList"""
```

Create `data/sprites.json`:
```json
{
  "sheets": {
    "enemies": "Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Enemies & Bosses - Enemies.png"
  },
  "sprites": {
    "goblin": {"sheet": "enemies", "x": 124, "y": 117, "w": 49, "h": 48},
    ...
  }
}
```

### 2.2 Enemy Sprite Mapping

**Enemies sheet layout (802×274):**
- Variable size sprites across two rows
- Positions identified using sprite picker tool

**Mapping process:**
1. Run `tools/sprite_picker.py`
2. Zoom in on target sprite area
3. Left-click drag to select the sprite region
4. Press Enter, type sprite name (e.g., "goblin", "dark_mage")
5. Repeat for all enemies in `data/enemies.json`

**Sprite ID mapping:**
- Enemy name "Goblin" → sprite_id "goblin"
- Enemy name "Dark Mage" → sprite_id "dark_mage"
- (lowercase, underscores for spaces)

### 2.3 Character Sprite Mapping (PENDING)

**Character sheet:** 465×718, multiple poses/directions per character

**Mapping process:**
1. Run `tools/sprite_picker.py` with characters sheet loaded (Tab)
2. Identify sprite positions for each character class
3. Add definitions to `data/sprites.json`
4. Update `game/scenes/overworld.py` to draw characters as sprites

**Todo:**
- Map character classes (warrior, mage, etc.) with idle/attack poses

### 2.4 Updating Renderers

Modify `game/battle/renderer.py` - draw enemies/party as sprites

Modify `game/scenes/overworld.py` - draw player/NPCs as sprites

---

## Phase 3: Maps + Tiles (PENDING)

### 3.1 Tile System

**Tile Assets:**

| Tileset | File | Notes |
|--------|-----|-------|
| Overworld | Various from assets/ | Grass, water, trees |
| Indoors | `assets/SNES - Final Fantasy 5 (JPN) - Tilesets - Indoors.png` | Floors, walls |
| Town | `assets/SNES - Final Fantasy 5 (JPN) - Tilesets - Town.png` | Buildings |

### 3.2 Tiled Map Integration

Create `game/tiles.py` and `game/tilemap.py` for tile rendering.

---

## Phase 1: Font + UI

| Sub-Phase | Status | New Files | Modified Files |
|-----------|--------|-----------|----------------|
| 1.1 | COMPLETED | `game/text.py`, `game/ui.py` | `game/engine.py`, `game/scenes/title.py` |
| 1.2 | COMPLETED | - | `game/battle/renderer.py`, `game/scenes/menu.py`, `game/scenes/overworld.py` |
| 1.3 | COMPLETED | - | `game/ui.py`, `game/scenes/menu.py` |

---

## Phase 2: Sprites

| Sub-Phase | Status | New Files | Modified Files |
|-----------|--------|-----------|----------------|
| 2.1 | COMPLETED | `tools/sprite_picker.py`, `game/sprites.py`, `data/sprites.json` | - |
| 2.2 | COMPLETED | `tools/sprite_picker.py`, `game/sprites.py`, `data/sprites.json` | `game/battle/renderer.py` |

---

## Technical Notes

### Font Registration (Critical)

The font registration must happen at module load time, BEFORE arcade.create_window() is called. The order of operations matters:

1. Python imports `game/engine.py`
2. `_register_font_early()` calls `pyglet.font.add_file(font_path)`
3. Later, `arcade.Window()` is created with GL context
4. Now `arcade.Text` and `arcade.draw_text` can use the custom font

If you try to register the font after the window is created, it won't work - pyglet has already initialized its font system.

### Font Naming

After calling `pyglet.font.add_file(path)`, access the font by its registered name:
```python
font = pyglet.font.load('Final Fantasy IV (Japan only)')
```

This name comes from the font file's metadata, not the filename.

---

## Sprite System Technical Notes

### Sprite Preloading (Arcade Limitation)

Arcade's SpriteList uses a texture atlas internally. Cropping the same sheet multiple times causes "texture not found in UVData" errors because all cropped textures share the same atlas reference.

**Workaround**: Extract each sprite region into a fully independent texture:

```python
def _preload_sprites(self):
    for sprite_id, sprite_def in self.definitions.items():
        cropped = sheet.crop(sx, sy, sw, sh)
        img = cropped.image

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)

        self.sprite_textures[sprite_id] = arcade.load_texture(buf)
```

This is less memory-efficient than true sprite sheet reuse, but avoids the atlas conflict.

### Drawing Method

Use `arcade.Sprite` with `SpriteList` instead of direct texture drawing:

```python
sprite = arcade.Sprite()
sprite.texture = texture
sprite.center_x = x
sprite.center_y = y
sprite.scale = scale

sprite_list = arcade.SpriteList()
sprite_list.append(sprite)
sprite_list.draw()
```

### Sprite Definitions

Sprite IDs map to enemy names (lowercase, underscores for spaces):
- "Goblin" → "goblin"
- "Dark Mage" → "dark_mage"

Each definition includes variable w/h (not fixed 16x16):
```json
{
  "goblin": {"sheet": "enemies", "x": 124, "y": 117, "w": 49, "h": 48}
}
```

### Sprite Picker Tool

`tools/sprite_picker.py` - Interactive tool for picking sprite regions:
- Zoom: scroll wheel (1x to 20x)
- Pan: middle-click drag or arrow keys
- Select: left-click drag
- Save: Enter (prompts for sprite name)
- Switch sheets: Tab

---

## Backward Compatibility

All changes maintain backward compatibility:
- If font not registered → system fonts used as fallback
- If sprite not defined → use colored rectangle
- If tile not defined → use color from tile_defs

---

## Asset Reference Summary

| Purpose | Asset File |
|---------|-----------|
| Font | `assets/onion-pixel.otf` |
| Characters | `assets/Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Characters - Characters.png` |
| Enemies | `assets/Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Enemies & Bosses - Enemies.png` |
| UI/Borders | `assets/Game Boy _ GBC - Final Fantasy Legend _ Makai Toushi SaGa - Backgrounds - Tilesets.png` |
| UI Reference | `assets/final-fantasy-legend-ii-screenshot-6_scale_800_700.jpg` |
| Map Tiles | Various in `assets/SNES - Final Fantasy 5 (JPN) - Tilesets - *.png` |
