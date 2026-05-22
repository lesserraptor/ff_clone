"""Tests for Tiled map conversion and loading."""

import os
import sys
import json

import pytest

from game.tiled_map_loader import load_tiled_map, gid_to_tile_id

MAPS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "maps")
JSON_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "maps.json")
MAPS_CONVERTED_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "maps_converted.json")


# ── helpers ──────────────────────────────────────────────────────────

def _load_json(path):
    with open(path, "r") as f:
        return json.load(f)


# ── .tmx file existence ─────────────────────────────────────────────

def test_load_tiled_map_exists():
    """Verify each .tmx file exists in assets/maps/."""
    data = _load_json(MAPS_CONVERTED_PATH)
    for map_id in data["maps"]:
        tmx_path = os.path.join(MAPS_DIR, f"{map_id}.tmx")
        assert os.path.exists(tmx_path), f"Missing .tmx for map: {map_id}"


# ── basic load ───────────────────────────────────────────────────────

def test_load_tiled_map_basic():
    """Load overworld_1.tmx, verify width=15, height=10, name matches."""
    tmx_path = os.path.join(MAPS_DIR, "overworld_1.tmx")
    m = load_tiled_map(tmx_path)
    assert m["width"] == 15
    assert m["height"] == 10
    assert m["name"] == "World Center"
    assert m["tile_size"] == 16
    assert m["id"] == "overworld_1"


# ── gids grid ────────────────────────────────────────────────────────

def test_load_tiled_map_gids():
    """Load a map, verify gids grid dimensions match width/height, all positive ints."""
    tmx_path = os.path.join(MAPS_DIR, "overworld_1.tmx")
    m = load_tiled_map(tmx_path)
    gids = m["gids"]
    assert len(gids) == m["height"]
    assert len(gids[0]) == m["width"]
    for row in gids:
        for gid in row:
            assert isinstance(gid, int)
            assert gid >= 0


# ── npcs ─────────────────────────────────────────────────────────────

def test_load_tiled_map_npcs():
    """Load town_1.tmx (has NPCs), verify npcs list is populated correctly."""
    tmx_path = os.path.join(MAPS_DIR, "town_1.tmx")
    m = load_tiled_map(tmx_path)
    npcs = m["npcs"]
    assert len(npcs) == 1, f"Expected 1 NPC, got {len(npcs)}"
    npc = npcs[0]
    # King at (4, 2) with script king_intro
    assert npc["x"] == 4, f"Expected NPC x=4, got {npc['x']}"
    assert npc["y"] == 2, f"Expected NPC y=2, got {npc['y']}"
    assert npc["script"] == "king_intro", f"Expected script=king_intro, got {npc.get('script')}"
    assert npc.get("name") == "King", f"Expected name=King, got {npc.get('name')}"


# ── exits ────────────────────────────────────────────────────────────

def test_load_tiled_map_exits():
    """Load overworld_1.tmx, verify exits list matches expected from maps.json."""
    data = _load_json(MAPS_CONVERTED_PATH)
    expected_exits = data["maps"]["overworld_1"]["exits"]

    tmx_path = os.path.join(MAPS_DIR, "overworld_1.tmx")
    m = load_tiled_map(tmx_path)
    exits = m["exits"]

    assert len(exits) == len(expected_exits), (
        f"Expected {len(expected_exits)} exits, got {len(exits)}"
    )

    for ex in exits:
        assert "x" in ex
        assert "y" in ex
        assert "dest_map" in ex
        assert "dest_x" in ex
        assert "dest_y" in ex
        assert "direction" in ex

    # Spot-check: first exit goes to overworld_2
    ow2_exits = [e for e in exits if e["dest_map"] == "overworld_2"]
    assert len(ow2_exits) == 1
    assert ow2_exits[0]["x"] == 1
    assert ow2_exits[0]["y"] == 5
    assert ow2_exits[0]["direction"] == "left"


# ── invalid file ─────────────────────────────────────────────────────

def test_load_tiled_map_invalid():
    """Attempt to load nonexistent .tmx, verify raises FileNotFoundError."""
    bogus = os.path.join(MAPS_DIR, "nonexistent_map.tmx")
    with pytest.raises(FileNotFoundError):
        load_tiled_map(bogus)


# ── overworld model integration ──────────────────────────────────────

def test_overworld_model_uses_tiled():
    """Create OverworldModel with mock engine, verify it loads a map."""
    from game.scenes.overworld_states import load_maps, load_enemies

    tile_defs, maps, scripts = load_maps()

    # Verify we loaded tile_defs from maps.json
    assert len(tile_defs) >= 9, f"Expected >=9 tile_defs, got {len(tile_defs)}"

    # Verify maps came from .tmx files
    assert "overworld_1" in maps, "overworld_1 not in loaded maps"
    assert "town_1" in maps, "town_1 not in loaded maps"
    assert "dungeon_1" in maps, "dungeon_1 not in loaded maps"

    m = maps["overworld_1"]
    expected_keys = {"id", "name", "width", "height", "tile_size", "gids", "tiles", "npcs", "exits"}
    assert expected_keys.issubset(m.keys()), f"Missing keys: {expected_keys - set(m.keys())}"

    assert m["width"] == 15
    assert m["height"] == 10
    assert m["name"] == "World Center"

    # gids and tiles should have matching dimensions
    assert len(m["gids"]) == m["height"]
    assert len(m["tiles"]) == m["height"]
    assert len(m["gids"][0]) == m["width"]


# ── gid_to_tile_id ───────────────────────────────────────────────────

def test_gid_to_tile_id():
    """Verify reverse GID→tile ID mapping covers all used GIDs."""
    # GID 3 (grass) → tile 0
    assert gid_to_tile_id(3) == 0
    # GID 15 (water) → tile 1
    assert gid_to_tile_id(15) == 1
    # Tree GIDs → tile 2
    assert gid_to_tile_id(1) == 2
    assert gid_to_tile_id(2) == 2
    assert gid_to_tile_id(9) == 2
    # GID 66 (path) → tile 3
    assert gid_to_tile_id(66) == 3
    # Fallback for unknown GID returns GID itself
    assert gid_to_tile_id(999) == 999
