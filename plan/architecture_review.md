# Architecture Review — FF Clone

An analysis of the current codebase architecture, identifying what's well-separated, where the pain points live, and what would need to change for a GBC → SNES re-theme (or any resolution/theme change).

---

## What's Already Well-Separated

| Layer | Where | Notes |
|-------|-------|-------|
| Game state (pure data) | `GameEngine`, `PartyMember`, `Actor` | No drawing deps |
| Battle logic | `BattleModel` | Zero arcade imports, pure combat |
| Battle states | `battle/states.py` | Return result codes, no drawing |
| Overworld logic | `OverworldModel` | Pure state, no arcade imports |
| Scene coordinator | `OverworldScene`, `BattleScene` | Delegates to model + renderer |
| Data loading | `engine.py` `load_game_data()` | Runs once at init, separated from scenes |
| Data-driven visuals | `ui_borders.json`, `sprites.json` | Layout/colors in data files |
| Centralized palette | `ui.py` `COLORS` dict | Single palette change-point |

---

## Problem Areas

### Tier 1 — Layout Constants Hardcoded Everywhere

This is the biggest blocker for resolution change (GBC 240×160 → SNES 256×224 or higher). Layout values are scattered across every renderer and scene as raw pixel numbers:

- `battle/renderer.py` lines 9-16: `BW=240, BH=160, MENU_H=BH*0.55, CHAR_BOX_W=BW*2/5`
- `battle/renderer.py` line 100: `cy = int(h * 0.72)` — enemy Y position
- `menu_states.py` passim: pixel positions like `146 * scale`, `120 * scale`, `32 * scale`
- `overworld_states.py` line 278: offset centering math
- `ui.py` `BORDER_PX=6` inside `draw_window`

**Suggested fix:** Extract all layout constants into a per-scene **layout config dict** with proportional positions (e.g., `"enemy_box": {"x": "40%", "w": "60%"}`). An "SNES theme" swaps the config.

---

### Tier 2 — Mixed Rendering Approaches (No Common Interface)

Different scenes draw in different ways with no shared contract:

- `BattleRenderer` is a class with `draw(model, state, ...)` — clean
- `OverworldRenderer` is a class in same file as `OverworldModel` — same-file coupling unnecessary
- `MenuState` subclasses each have `draw(self, w, h, scale)` — 6 different draw methods
- `SpriteAtlas.draw()` creates one-shot `SpriteList` per frame — arcade API leak
- `text.py` wraps `arcade.Text`

There is no `Renderer(ABC)` or `SceneRenderer` protocol. Every scene reinvents drawing. To re-theme, you'd touch every draw method.

**Suggested fix:** Define abstract `SceneRenderer` or at minimum a `LayoutContext` all draw methods accept (scale, viewport, theme colors).

---

### Tier 3 — `engine.py` is a God Module

A single file holds unrelated concerns:

| Concern | Approx lines |
|---------|-------------|
| Scene registry (`SCENES`) | 1 |
| `GameEngine` (state holder) | ~95 |
| Data loading (`load_game_data`) | ~10 |
| Global data dicts (`ITEM_DATA`, etc.) | ~15 |
| `DEFAULT_PARTY` | ~15 |
| `calc_party_stats()` | ~30 |
| `get_item()` | ~10 |
| `register_scene()` | ~5 |

**Suggested fix:** Split into `game/state.py` (`GameEngine`), `game/data.py` (data loading + dicts), `game/stats.py` (`calc_party_stats`), `game/scene_registry.py` (`SCENES` + `register_scene`).

---

### Tier 4 — Model ↔ Renderer Direct Property Access

Examples:

```python
# battle/renderer.py — direct access to model.enemies, model.party, model.rewards
# overworld_states.py renderer — direct access to model.map_data["gids"]
```

Any change to model field names silently breaks renderers.

**Suggested fix:** Formalize a **view model** or **render state** — a plain dict/dataclass the model produces and the renderer consumes. `model.get_render_state()` returns `{"enemies": [...], "party": [...], "animations": [...]}`.

---

### Tier 5 — Specific Detail Issues

1. `SpriteAtlas.draw()` creates new `arcade.Sprite()` + `SpriteList` per call — GC churn, couples loading to drawing. Better: atlas returns textures, renderer draws.

2. Level-up logic duplicated: `BattleModel.apply_level_ups()` exists but `BattleScene._apply_victory()` does its own level-ups inline. Dead code risk.

3. Font path `"assets/onion-pixel.otf"` hardcoded. Changing font requires grep-and-replace.

4. No event system for scene transitions — re-theme wanting fade/wipe effects has no hook.

5. `OverworldModel` constructor does file I/O (`load_maps`, `load_enemies`). Model should receive data, not load it.

---

## Conclusion / Summary for Re-Theming

Re-theming GBC → SNES is **moderate-to-high effort** because:

- Layout math everywhere (40+ hardcoded coordinate expressions across 5+ files)
- No abstract renderer interface to swap
- Viewport/resolution assumptions in `main.py` constants
- Scene transitions have no hook for effects

**Low-effort changes that would help most:**

1. Extract all layout constants to per-scene config dicts
2. Define a `RenderContext` / `LayoutContext` carrying scale, viewport, theme colors, font
3. Add a simple event bus for scene transitions (fade-out/fade-in hooks)
4. Formalize model → view data flow (render state dicts or view models)
5. Split `engine.py` into focused modules
