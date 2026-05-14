# Phase 4 — Battle Menu Visual Polish & Control Fixes

**Target files**: `game/battle/renderer.py`, `game/battle/states.py`, `game/scenes/battle.py`
**Model untouched** — pure view/controller work.

---

## 4.1 Layout Zones

Current layout broken: `draw_party_area` and `draw_command_bar` both draw at `y=0, h=h//4` (bottom 25%). They fight for same space. Fix with 4 distinct vertical zones:

```
+--------------------------------------------------+
|  ENEMY AREA (top 58%)                             |
|    [Goblin]       [Slime]                        |
|    HP ████████     HP ████████                    |
|    ── ground line at ~42% height ──              |
|                                                   |
+--------------------------------------------------+
|  MESSAGE STRIP (~8%, thin banner)                 |
|  "Goblin attacks for 5 damage!"                   |
+--------------------------------------------------+
|  PARTY STATUS (~12%)                              |
|  [Warrior HP ████ MP ████] [Wizard HP ████ ...]  |
+--------------------------------------------------+
|  COMMAND BAR (~8%)                                |
|  ▶ FIGHT   MAGIC   ITEM   RUN                     |
+--------------------------------------------------+
```

Zone calculations (base 240×160, scaled):

```
SCREEN_H = h  (e.g. 160 @ 1×, 640 @ 4×)

enemy_top    = h * 0.58       # top of enemy zone (= y_top of screen)
enemy_bottom = h * 0.00       # bottom of enemy zone (= y=0, in screen coords)
                        ─ wait, arcade y=0 is bottom.

Re-do in arcade coords (y=0 at bottom):

zone            y_start  y_end    height
──────────────────────────────────────────
command_bar     0        h*0.08   8%
party_status    h*0.08   h*0.20   12%
message_strip   h*0.20   h*0.28   8%
enemy_area      h*0.28   h        72%
──────────────────────────────────────────
```

Message strip only visible when `message` is non-empty. Otherwise enemy area extends down to `h*0.20`.

### Changes in `renderer.py`

- **`draw()`**: Redraw order: background → enemy_area → message_strip (if msg) → party_status → command_bar (if command/spell_select state). Remove `draw_window` calls that hardcode `h//4`.
- **`draw_enemy_area()`**: Change bounds from `(0, h//4, w, h*3//4)` to `(0, h*20//100, w, h*80//100)` (or thinner when message visible).
- **`draw_party_area()`**: Change bounds from `(0, 0, w, h//4)` to `(0, h*8//100, w, h*12//100)`. Convert from 4-column grid to 2-row horizontal bar:
  - Row 1: Member 0 name + HP bar/numbers, Member 1 name + HP bar/numbers
  - Row 2: Member 2 name + HP bar/numbers, Member 3 name + HP bar/numbers
  - Use `draw_window` around the whole party zone
- **`draw_command_bar()`**: Change bounds from `(0, 0, w, h//4)` to `(0, 0, w, h*8//100)`. Add `▶` cursor via `draw_cursor()` from `game/ui.py`.
- **New `draw_message_strip()`**: Thin banner at `y = h*20//100` to `y = h*28//100`, only when message non-empty. Use `draw_window` with darker fill.

---

## 4.2 Visual Polish

### Battlefield Background

Current: plain black + colored rects. Replace with:

1. **Sky gradient** (top 40%): dark blue → dark purple gradient. Use `arcade.draw_lrbt_rectangle_filled` with color interpolation in a loop:
   ```python
   steps = 8
   for i in range(steps):
       t = i / steps
       r = int(top_r + (bot_r - top_r) * t)
       g = int(top_g + (bot_g - top_g) * t)
       b = int(top_b + (bot_b - top_b) * t)
       y0 = sky_top + (sky_bot - sky_top) * t / steps
       y1 = sky_top + (sky_bot - sky_top) * (t + 1) / steps
       arcade.draw_lrbt_rectangle_filled(0, w, y0, y1, (r, g, b))
   ```
2. **Ground** (bottom 60%): dark green/brown rect. Single fill color `(20, 60, 20)` or `(40, 30, 20)`.
3. **Ground line**: 1px bright line at ~40% height as horizon. Color `(100, 120, 80)`.

Only draw when no message occupies the enemy area (or draw behind everything).

### Enemy Display

- `draw_enemy_area()`: sprite drawn at larger scale (`1.2*scale` vs current `scale`)
- **HP bar under each enemy**: use `draw_hp_bar()` from `game/ui.py`. Position below sprite, centered.
- Enemy name above sprite in small text.
- Dead enemies: gray sprite + empty HP bar.
- Spacing: center each enemy in its column. If 1 enemy → center screen. If 2 → thirds.

```
    ┌──────┐          ┌──────┐
    │Goblin│          │ Slime│
    └──────┘          └──────┘
   HP ████████ 8/20   HP ██████ 6/12
```

### Flash Animation

Current: 4 flashes at 0.15s. Keep cycle but:

- **Party flash**: thick gold outline (`(255, 220, 0)`, 3px) around the acting member's party box.
- **Enemy flash**: thick red outline (`(255, 60, 60)`, 3px) around the acting enemy.
- Optional: brief screen shake (offset draw position by ±2px on flash frames). Low priority.

### Message Display

Replace centered overlay (`h//2`) with dedicated message strip at `y = h*20//100`:

- `draw_message_strip()`: call `draw_window()` with `(0, h*20//100, w, h*8//100, scale, fill=(10,10,30), border=(160,160,160))`.
- Text left-aligned with padding, not centered.
- Font size `7*scale` for GBC feel.

Victory/defeat messages remain full-screen centered boxes (they're rare, feel dramatic).

### Party Status

Zone `h*8//100` to `h*20//100`:

- Horizontal bar divided into 4 member slots (or 2 rows of 2 if cramped).
- Each slot: name (truncated to 6 chars), HP bar + "HP 40/50", MP bar + "MP 12/30" (if mp_max>0).
- Use `draw_hp_bar` and `draw_mp_bar` from `game/ui.py` with `width=w//4 - 12*scale`.
- Dead members: gray text, empty bars.
- Active member indicator (whose turn): gold border around that slot, or pulsing arrow `▶` beside name.
- Use `draw_window` around entire party zone for border.

```
┌──────────────────────────────────────────────────────┐
│ [Warrior]     HP ████████ 40/50  MP ████ 10/30     │
│ [Wizard]      HP ████████ 35/35  MP ████ 30/30     │
│ [Rogue]  DEAD HP ░░░░░░░░  0/40                     │
│ [Healer]      HP ████████ 30/30  MP ████ 40/40     │
└──────────────────────────────────────────────────────┘
```

### Font Sizing

Tune for GBC feel at 240×160 base:

| Element | Size (base) | Scaled |
|---------|------------|--------|
| Enemy name | 6px | `6 * scale` |
| Enemy HP text | 5px | `5 * scale` |
| Party member name | 6px | `6 * scale` |
| Party HP/MP numbers | 5px | `5 * scale` |
| Command options | 7px | `7 * scale` |
| Message text | 7px | `7 * scale` |
| Spell list | 6px | `6 * scale` |

Font: `onion-pixel.ttf` (loaded in `game/__init__.py` via `init_game()`).

---

## 4.3 Control Fixes

### 4.3.1 CommandState: Add UP Handler

**File**: `game/battle/states.py`, `CommandState.update()`

Current: only listens to DOWN/Z/X. Add UP handler:

```python
if inpt.is_just_pressed(key.UP):
    self.selection = (self.selection - 1) % len(self.options)
elif inpt.is_just_pressed(key.DOWN):
    self.selection = (self.selection + 1) % len(self.options)
```

This gives bidirectional navigation: UP = previous option, DOWN = next option.

### 4.3.2 TargetState: Swap UP/DOWN → LEFT/RIGHT

**File**: `game/battle/states.py`, `TargetState.update()`

Enemies laid out horizontally (spaced across screen width), but target nav uses UP/DOWN. Fix:

```python
if inpt.is_just_pressed(key.RIGHT):
    self.selection = (self.selection + 1) % len(targets)
elif inpt.is_just_pressed(key.LEFT):
    self.selection = (self.selection - 1) % len(targets)
```

Keep DOWN as an alias for RIGHT (muscle memory / vertical list feel optional), but primary is LEFT/RIGHT.

### 4.3.3 SpellSelectState Cancel Bug

**File**: `game/battle/states.py`, `SpellSelectState.update()` + `game/scenes/battle.py`, dispatch

`SpellSelectState.update()` line returns `"command"` on X key. But `_handle_result("command")` doesn't match `RESULT_DISPATCH` (no `"command"` key) and doesn't start with `"message:"`. So nothing happens — state stays stuck.

Fix: route `"command"` return value in `_handle_result`. Either:

- Add `"command": "_handle_command"` to `RESULT_DISPATCH` that transitions to command state:

  ```python
  def _handle_command(self):
      self.state = "command"
      self.current_state_obj = CommandState(self.current_party_idx)
  ```

  Or handle it inline in `_handle_result`:

  ```python
  if result == "command":
      self.state = "command"
      self.current_state_obj = CommandState(self.current_party_idx)
      return
  ```

- Alternative: change string to `"target_enemy"`-style naming, e.g. the existing code path works if we route it as a dispatch key. But simplest: add `"command"` key to `RESULT_DISPATCH`.

### 4.3.4 TargetState: LEFT/RIGHT Wrap

Already handled by modulo: `% len(targets)`. Verify alive-enemy index list is correct.

### 4.3.5 Visual Cursor on Command Bar

**File**: `game/battle/renderer.py`, `draw_command_bar()`

Replace color-only selection with cursor arrow:

```python
if i == selection:
    draw_cursor(x - 12 * scale, y, scale, COLORS["cursor"])
```

Arrow `▶` points at selected option. Keep yellow highlight on selected text too (dual signal).

---

## 4.4 Spell List UI Redesign

Currently draws at `y = h // 4` overlapping everything. Fix:

### Layout

```
┌───────────────────────────────────────┐
│  ENEMY AREA (visually dimmed behind)  │
│                                       │
│  ┌── Spell List Window ──────────┐   │
│  │  Wizard   MP 30/30            │   │
│  │                               │   │
│  │  ▶ Fire   MP-5                │   │
│  │    Ice   MP-8                 │   │
│  │    Thunder   MP-12 (dim)      │   │  ← not enough MP
│  │    Cure   MP-10               │   │
│  └───────────────────────────────┘   │
│                                       │
└───────────────────────────────────────┘
```

### Changes in `renderer.py`

- `draw_spell_list()`: Remove hardcoded `y = h // 4`. Instead:
  - Draw semi-transparent overlay over enemy area (darken it).
  - Draw spell window centered in enemy zone: `box_w = w * 0.6`, `box_h = min(len(spells) * 14 * scale + 24 * scale, h * 0.4)`.
  - Title line: `"{member.name}  MP {mp}/{mp_max}"` at top of window.
  - Each spell: name + `MP-{cost}`. Cursor `▶` via `draw_cursor()`.
  - Gray/dim color for spells where `member.mp < mp_cost`.

- Add overlay helper: `_draw_overlay()` that fills the area behind the spell window with a dark semi-transparent rect to dim the battlefield.

---

## Implementation Order

### Step 1: Layout zones (4.1)
- `renderer.py`: Rewrite zone calculations. Split `draw_party_area` into `draw_party_status` and `draw_command_bar` at different y ranges. Add `draw_message_strip`. Fix `draw_enemy_area` bounds.

### Step 2: Control fixes (4.3)
- `states.py`: UP in CommandState, LEFT/RIGHT in TargetState.
- `battle.py`: Fix `"command"` dispatch in `_handle_result`.

### Step 3: Background & enemy polish (4.2)
- `renderer.py`: `draw_background()` with gradient + ground line.
- `renderer.py`: HP bars under enemies, bigger sprites.

### Step 4: Command bar cursor (4.3.5)
- `renderer.py`: `draw_cursor()` in `draw_command_bar()`.

### Step 5: Spell list UI (4.4)
- `renderer.py`: Rewrite `draw_spell_list()` with overlay + centered window.

### Step 6: Message strip (4.2 messaging)
- `renderer.py`: Wire `draw_message_strip()` into `draw()`.

### Step 7: Party indicator polish
- `renderer.py`: Gold thick outline or pulsing arrow on current member's slot.

---

## Test

```bash
python3 main.py
```

Trigger battle by walking on overworld. Verify:
- [ ] Zones don't overlap — party status and command bar are separate
- [ ] UP works in command state (reverses direction)
- [ ] LEFT/RIGHT work in target state
- [ ] X from spell list goes back to command (not stuck)
- [ ] HP/MP bars visible for party and enemies
- [ ] Command bar shows cursor arrow
- [ ] Spell list overlays enemy area without clipping
- [ ] Message strip shows at correct zone (not covering enemies)
- [ ] Battlefield has gradient background
- [ ] Party indicator clearly shows whose turn
