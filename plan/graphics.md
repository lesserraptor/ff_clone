# Graphics Implementation Plan

## Overview

Replaceable graphics system: swap assets without modifying game code. Three phases — font/UI (done), sprites (partial), maps/tiles (pending). Each phase has data-driven definitions (JSON) so asset changes = file swaps, not code edits.

---

## Phase 1: Font + UI System (COMPLETED)

### 1.1 Font System

**Asset:** `assets/onion-pixel.otf`
**Registered name:** "Onion Pixel" (from font file metadata)
**File:** `game/text.py`

Font registration happens at module load time via `pyglet.font.add_file()`. This must run *before* `arcade.Window()` creates a GL context, because pyglet finalizes its font system at window creation.

The `game/text.py` module exposes:

| Function | Purpose |
|----------|---------|
| `load_font()` | Registers font if needed, returns "Onion Pixel" |
| `create_text(text, x, y, color, size, anchor_x, anchor_y)` | Returns `arcade.Text` with custom font |
| `draw_text(text, x, y, color, size, scale, anchor_x, anchor_y)` | Calls `arcade.draw_text` with custom font (for one-off text) |
| `get_text_width(text, size, scale)` | Approximate pixel width |
| `get_text_height(size, scale)` | Returns `size * scale` |

Key implementation detail: `_register_font()` uses a `_font_registered` guard so loading happens at most once. The font path is `assets/onion-pixel.otf`.

### 1.2 UI System

**File:** `game/ui.py`
**Data:** `data/ui_borders.json`
**Reference:** `plan/menu_border_desc.md` (pixel pattern documentation)

**COLORS dict** (derived from FF Legend II reference image `assets/final-fantasy-legend-ii-screenshot-6_scale_800_700.jpg`):

| Key | RGB | Usage |
|-----|-----|-------|
| `box_fill` | (48, 48, 160) | Menu/window background |
| `box_border` | (160, 160, 160) | Window border |
| `text` | (255, 255, 255) | Default text |
| `cursor` | (255, 255, 0) | Selection cursor |
| `enemy` | (255, 48, 48) | Enemy HP/name |
| `player_hp` | (48, 112, 208) | Player HP text |
| `hp_fill` | (0, 200, 0) | HP bar fill |
| `hp_empty` | (80, 80, 80) | HP bar background |
| `mp_fill` | (48, 48, 255) | MP bar fill |
| `mp_empty` | (80, 80, 80) | MP bar background |

**Drawing functions:**

| Function | Description |
|----------|-------------|
| `draw_window(x, y, w, h, scale, fill_color, border_color)` | Blue box with pixellated 3D border |
| `draw_window_centered(cx, cy, w, h, scale, fill_color, border_color)` | Same, centered on (cx, cy) |
| `draw_cursor(x, y, scale, color)` | Yellow triangle cursor |
| `draw_hp_bar(current, max, x, y, scale, width, height)` | Green HP bar with border |
| `draw_mp_bar(current, max, x, y, scale, width, height)` | Blue MP bar with border |
| `draw_bordered_box(x, y, w, h, scale, fill_color, border_color)` | Simple filled box with outline |
| `draw_pixellated_border(x, y, w, h, scale, border_color)` | Low-level pixellated 3D border |

**Border system** — data-driven from `data/ui_borders.json`. The JSON defines a 3×3 grid of 6×6 pixel blocks:

```
+-------+-------------------+-------+
| TL    | repeat top edge   | TR    |
| 6×6   | (w-12) wide       | 6×6   |
+-------+-------------------+-------+
| repeat|                   | repeat|
| left  |  transparent      | right |
| edge  |  (w-12 × h-12)    | edge  |
| 1 px  |                   | 1 px  |
+-------+-------------------+-------+
| BL    | repeat bot edge   | BR    |
| 6×6   | (w-12) wide       | 6×6   |
+-------+-------------------+-------+
```

Character mapping: `w` = light color, `g` = mid color, `b` = dark color, `t` = transparent. Colors are derived from the `border_color` parameter at runtime by adding/subtracting brightness offsets.

See `plan/menu_border_desc.md` for complete pixel patterns and `data/ui_borders.json` for the actual data.

### 1.3 Text Caching Pattern

All renderers avoid `arcade.draw_text` PerformanceWarning by caching `arcade.Text` objects. Two variants exist:

**Per-scale dict cache** (`overworld_states.py`, `menu.py`):
```python
def _get_text(self, key, text, x, y, color, size, anchor_x, anchor_y):
    scale = self._prev_scale
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

**Single-key cache** (`title.py`):
```python
def _get_text(self, key, text, size, color, anchor_x="center"):
    scale = self.engine.get_scale()
    if self._prev_scale != scale or key not in self._texts:
        self._texts[key] = create_text(text, 0, 0, color, size, anchor_x=anchor_x, anchor_y="center")
        self._prev_scale = scale
    return self._texts[key]
```

**Hybrid with two cache dicts** (`battle/renderer.py`):
- `_get_text(cache, key, text, x, y, color, size, anchor_x, anchor_y)` — single dict per purpose
- `_get_text_simple(cache, key, text, x, y, color, size, anchor_y)` — nested `{scale: {key: text}}` dict

All renderers set `self._prev_scale = scale` at end of `draw()`.

### 1.4 Renderers Updated

All scene renderers use `create_text()` from `game/text.py` and `draw_window()`/`COLORS` from `game/ui.py`:

- `game/scenes/title.py` — title screen text
- `game/scenes/menu.py` — menu windows, party stats, items
- `game/scenes/overworld_states.py` — map name, dialog boxes
- `game/battle/renderer.py` — enemy names, party HP/MP, command bar, message boxes, spell lists

### 1.5 Pixel Art Filtering

**Problem:** Sprites looked blurry when drawn at integer scales (2x, 3x, 4x). Default OpenGL texture filtering (GL_LINEAR) interpolates between pixels, smoothing pixel art.

**Root cause:** `arcade.SpriteList` creates an internal texture atlas with default `filter = (GL_LINEAR, GL_LINEAR)` → `(9729, 9729)`.

**Fix:** Pass `pixelated=True` to `SpriteList.draw()`:

```python
sprite_list.draw(pixelated=True)
```

This sets the atlas texture filter to `(GL_NEAREST, GL_NEAREST)` → `(9728, 9728)` before rendering, preserving crisp pixel edges.

**Scope:** Every `SpriteList.draw()` call must use `pixelated=True`:
- `game/sprites.py` — `SpriteAtlas.draw()` method
- `game/scenes/overworld_states.py` — any direct SpriteList usage (none currently, goes through atlas)
- `game/battle/renderer.py` — any direct SpriteList usage

**Note:** This only affects sprites drawn via `SpriteList`. Text drawn via `arcade.Text` uses a separate render path (font atlas) and is unaffected.

---

## Phase 2: Sprite System (PARTIALLY COMPLETED)

### 2.1 Sprite Atlas

**File:** `game/sprites.py`
**Tool:** `tools/sprite_picker.py` (interactive region selector)

**Class:** `SpriteAtlas`

| Method | Purpose |
|--------|---------|
| `load_sheet(name, filename)` | Load a full sprite sheet as `arcade.Texture` |
| `load_definitions(json_path)` | Load JSON, load sheets, preload all sprites |
| `get_sprite(sprite_id)` | Returns definition dict or None |
| `draw(sprite_id, x, y, scale)` | Draw sprite via `arcade.Sprite` + `SpriteList` |
| `has_sprite(sprite_id)` | Check if sprite texture exists |

**Singleton:** `get_sprite_atlas()` — caches one global instance, loads definitions from `data/sprites.json`.

**Sprite preloading workaround** (arcade SpriteList atlas limitation):

Arcade's `SpriteList` uses an internal texture atlas. Cropping the same sheet multiple times causes "texture not found in UVData" errors because all cropped textures share the same atlas reference.

Workaround — extract each sprite into a fully independent texture:
```python
cropped = sheet.crop(sx, sy, sw, sh)
img = cropped.image
buf = io.BytesIO()
img.save(buf, format='PNG')
buf.seek(0)
self.sprite_textures[sprite_id] = arcade.load_texture(buf)
```

This is less memory-efficient than true sprite sheet reuse, but avoids the atlas conflict.

**Drawing method:**
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

### 2.2 Enemy Sprite Mapping (COMPLETED)

**Data file:** `data/sprites.json`

Enemy sprite definitions using the enemies sheet (`assets/Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Enemies & Bosses - Enemies.png`, 802×274):

| Sprite ID | Region | Size |
|-----------|--------|------|
| `goblin` | (124, 117) | 49×48 |
| `skeleton` | (237, 117) | 47×48 |
| `slime` | (85, 21) | 32×32 |
| `wolf` | (68, 117) | 49×48 |
| `imp` | (645, 4) | 32×49 |
| `dark_mage` | (405, 117) | 48×48 |

**ID convention:** enemy name lowercase, spaces → underscores (e.g., "Dark Mage" → `dark_mage`).

**Usage in battle:** `game/battle/renderer.py` calls `get_sprite_atlas().has_sprite(sprite_id)` then `draw()`; falls back to colored rectangle if sprite missing.

**Mapping process** (for future additions):
1. Run `tools/sprite_picker.py`
2. Zoom (scroll wheel), pan (middle-click drag / arrows)
3. Left-click drag to select region
4. Press Enter, type sprite name
5. Tab to switch between loaded sheets
6. Saves to `data/sprites.json`

### 2.3 Character Sprite Mapping (PARTIALLY COMPLETED)

**Character sheet:** `assets/Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Characters - Characters.png` (465×718)

**COMPLETED — Front-facing idle sprites:**
- [x] Run `tools/sprite_picker.py` on characters sheet
- [x] Map front-facing idle pose for each class → `warrior`, `wizard`, `rogue`, `healer`
- [x] Add sprite definitions to `data/sprites.json` under `"characters"` sheet
- [x] Add characters sheet filename to `data/sprites.json` `"sheets"` section

**PENDING — Directional + animation frames:**

Each character needs frames for all 4 walking directions (down, left, right, up), with 2 frames per direction (standing + walk frame) for animation.

**ID convention:** `{class}_{direction}_{frame}`

| Direction | Frame 0 (idle) | Frame 1 (walk) |
|-----------|---------------|----------------|
| down | `warrior_dn_0` | `warrior_dn_1` |
| left | `warrior_lf_0` | `warrior_lf_1` |
| right | `warrior_rt_0` | `warrior_rt_1` |
| up | `warrior_up_0` | `warrior_up_1` |

Same pattern for wizard, rogue, healer.

**TODO:**
- [ ] Map directional frames (down, left, right, up) for each class using sprite_picker
- [ ] Map walk animation frame (frame 1) for each direction for each class
- [ ] Verify all 32 sprites (4 classes × 4 directions × 2 frames) are defined in `data/sprites.json`

### 2.4 Updating Renderers

**COMPLETED:**
- `game/battle/renderer.py` — draws enemy sprites with fallback to colored rectangles
- `game/scenes/overworld_states.py` — player sprite draws from atlas (front-facing only, no animation)

**PENDING:**
- [ ] `game/scenes/overworld_states.py` — select sprite based on `model.facing` direction (dn/lf/rt/up)
- [ ] `game/scenes/overworld_states.py` — animate between frame 0 ↔ frame 1 during movement (walk cycle)
- [ ] `game/scenes/overworld_states.py` — replace red rectangle NPCs with NPC sprites from atlas (requires NPC sprite IDs in maps.json)

### 2.5 Overworld Sprite Animation System

**File:** `game/scenes/overworld_states.py`

The overworld sprite animation has two axes:
1. **Direction**: Choose which sprite to draw based on `model.facing` ("down", "left", "right", "up")
2. **Frame**: Alternate between frame 0 (idle) and frame 1 (walk) during movement

**Direction → sprite suffix mapping:**
| facing value | suffix |
|-------------|--------|
| `"down"` | `_dn_` |
| `"left"` | `_lf_` |
| `"right"` | `_rt_` |
| `"up"` | `_up_` |

**Animation logic (pseudocode):**
```
sprite_id = f"{model.player_sprite_id}_{dir_suffix}{frame}"
where:
  dir_suffix = direction_map[model.facing]
  frame = 0 if not model.is_moving else (int(model.move_progress * 2) % 2)
```

If a specific directional/walk sprite doesn't exist in the atlas, fall back to the base front-facing idle sprite (e.g., `warrior`).

**Frame timing:** During movement (`model.is_moving == True`), `move_progress` goes from 0.0 to 1.0. The frame toggles at 0.5, so the sprite alternates between frame 0 and frame 1 during each tile-step. When idle, always show frame 0.

**Sprite count:** 32 sprites total (4 classes × 4 directions × 2 frames) + 4 fallback sprites (base front-facing).

---

## Phase 3: Maps + Tiles (PENDING)

No files exist yet for tile/tilemap system. All tileset PNGs need to be sourced.

### 3.1 Tile System

**TODO:**
- [ ] Create `game/tiles.py` — tile loading and rendering
- [ ] Create `game/tilemap.py` — Tiled JSON map format loader + renderer
- [ ] Define tile size (16×16 base expected)
- [ ] Support tile layers (ground, objects, collisions)

**Potential assets (need to be sourced):**
- Overworld tiles (grass, water, trees, mountains)
- Town tiles (buildings, walls, floors)
- Indoor tiles (floors, walls, stairs)

No tileset files currently exist in `assets/`.

### 3.2 Tiled Map Integration

**TODO:**
- [ ] Parse Tiled JSON format (`.tmj` / `.json`)
- [ ] Tile layer rendering from sprite atlas
- [ ] Collision layer support
- [ ] Object layer support (chests, NPC triggers, exits)
- [ ] Replace current code-defined `maps.json` text-based tile system

Current overworld tile system (`game/scenes/overworld_states.py`) uses a JSON-based map format with custom `tile_defs` (color + walkable flag). This works but is primitive — no tile images, just colored rectangles.

---

## Backward Compatibility

All systems degrade gracefully:

- **Font missing** (`onion-pixel.otf` not found) → `load_font()` returns None → `create_text()`/`draw_text()` skip silently. Fallback to arcade system font is NOT currently implemented (no explicit fallback font_name set).
- **Sprite not defined** → `has_sprite()` returns False → renderers draw colored rectangle fallback
- **Tile not defined** → use color from `tile_defs` with default gray

---

## Technical Notes

### Font Registration Order (Critical)

1. Python imports `game/text.py` (anytime before arcade window)
2. `_register_font()` calls `pyglet.font.add_file(font_path)`
3. Later, `arcade.Window()` is created with GL context
4. Now `arcade.Text` / `arcade.draw_text` can use custom font by name

Registering *after* window creation fails — pyglet has already initialized its font system.

### Font Naming

After `pyglet.font.add_file(path)`, access by the name embedded in the font file's metadata (not the filename): `font = pyglet.font.load('Onion Pixel')`.

### Sprite Preloading (Arcade Limitation)

Arcade `SpriteList` internal texture atlas reuses texture regions. Cropping the same sheet → "texture not found in UVData". Workaround: crop → BytesIO → `arcade.load_texture(buf)` to create fully independent textures.

### Sprite Definition Format

Sprites have variable width/height (not fixed 16×16):
```json
{
  "goblin": {"sheet": "enemies", "x": 124, "y": 117, "w": 49, "h": 48}
}
```

### Border 3×3 Grid Layout

Implemented in `game/ui.py` → `draw_pixellated_border()`. At scale S, border thickness is `6 × S` pixels on each side. See `plan/menu_border_desc.md` for ASCII diagrams and `data/ui_borders.json` for pixel data.

---

## Asset Reference Summary

| Purpose | Filename |
|---------|----------|
| Font (OTF) | `assets/onion-pixel.otf` |
| Font (TTF fallback) | `assets/onion-pixel.ttf` |
| Characters sprite sheet | `assets/Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Characters - Characters.png` |
| Enemies sprite sheet | `assets/Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Enemies & Bosses - Enemies.png` |
| UI reference image | `assets/final-fantasy-legend-ii-screenshot-6_scale_800_700.jpg` |
| Border JSON data | `data/ui_borders.json` |
| Sprite definitions JSON | `data/sprites.json` |
| Border pixel patterns doc | `plan/menu_border_desc.md` |
