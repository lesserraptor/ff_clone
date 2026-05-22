"""Load Tiled .tmx map files into dict format compatible with the overworld system.

Uses pytiled_parser (dependency of arcade) for parsing .tmx files.

The loaded dict matches the shape expected by OverworldModel and OverworldRenderer:
  gids, tiles, width, height, npcs, exits, name, id, tile_size
"""

import os

from pytiled_parser import parse_map
from pytiled_parser.layer import ObjectLayer, TileLayer


# Reverse mapping: GID → logical tile ID (0–9 from tile_defs in maps.json).
# Derived from convert_maps.py TILE_TO_GID + tree expansion.
# Used so the returned "tiles" grid has values tile_defs can look up.
_GID_TO_TILE_ID = {
    1: 2,   # tree_canopy_border       → Tree (id=2)
    2: 2,   # tree_trunk               → Tree (id=2)
    3: 0,   # grass / sand             → Grass (id=0)
    5: 4,   # floor / brick floor      → Floor (id=4)
    7: 5,   # wall                     → Wall (id=5)
    8: 8,   # mountain / dark trim     → Mountain (id=8)
    9: 2,   # tree_canopy_center       → Tree (id=2)
    12: 9,  # bridge / vertical stone  → Bridge (id=9)
    15: 1,  # water / solid gray       → Water (id=1)
    16: 6,  # door / doorway           → Door (id=6)
    66: 3,  # path / solid ground      → Path (id=3)
}

# Which GIDs are walkable (mirrors tile_defs). Fallback True for unknown GIDs.
_GID_WALKABLE = {
    1: False, 2: False, 3: True, 5: True, 7: False,
    8: False, 9: False, 12: True, 15: True, 16: True, 66: True,
}


def gid_to_tile_id(gid: int) -> int:
    """Convert a visual GID back to a logical tile ID (0–9)."""
    return _GID_TO_TILE_ID.get(gid, gid)


def gid_is_walkable(gid: int) -> bool:
    """Return walkability for a GID (from tile_defs equivalent)."""
    return _GID_WALKABLE.get(gid, True)


def _infer_tiles_from_gids(gids):
    """Build a 2D grid of logical tile IDs from the GID grid."""
    return [[gid_to_tile_id(gid) for gid in row] for row in gids]


def _get_tile_size(parsed):
    """Get tile size in pixels from parsed map."""
    return int(parsed.tile_size.width)


def _get_obj_prop(obj, key, default=None):
    """Safely read a custom property from a TiledObject's properties dict."""
    if obj.properties and key in obj.properties:
        return obj.properties[key]
    return default


def load_tiled_map(tmx_path: str) -> dict:
    """Load a .tmx file and return map data dict compatible with overworld system.

    Returns dict with keys:
        id, name, width, height, tile_size, gids, tiles, npcs, exits
    """
    if not os.path.exists(tmx_path):
        raise FileNotFoundError(f"TMX file not found: {tmx_path}")

    from pathlib import Path
    parsed = parse_map(Path(tmx_path))

    map_id = os.path.splitext(os.path.basename(tmx_path))[0]
    tile_size = _get_tile_size(parsed)
    width = int(parsed.map_size.width)
    height = int(parsed.map_size.height)

    # Map display name from custom property or fallback to file stem
    name = map_id
    if parsed.properties and "name" in parsed.properties:
        name = str(parsed.properties["name"])

    gids = []
    npcs = []
    exits = []

    for layer in parsed.layers:
        if isinstance(layer, TileLayer) and layer.data:
            # layer.data is List[List[int]] — GID grid in row-major order
            gids = layer.data

        elif isinstance(layer, ObjectLayer):
            if layer.name == "NPCs":
                for obj in layer.tiled_objects:
                    tile_x = int(obj.coordinates.x // tile_size)
                    tile_y = int(obj.coordinates.y // tile_size)
                    npc = {"x": tile_x, "y": tile_y}

                    npc_name = _get_obj_prop(obj, "name")
                    if npc_name is not None:
                        npc["name"] = str(npc_name)
                    elif obj.name:
                        npc["name"] = obj.name

                    script = _get_obj_prop(obj, "script")
                    if script is None:
                        script = _get_obj_prop(obj, "script_id")
                    if script is not None:
                        npc["script"] = str(script)

                    npcs.append(npc)

            elif layer.name == "Exits":
                for obj in layer.tiled_objects:
                    tile_x = int(obj.coordinates.x // tile_size)
                    tile_y = int(obj.coordinates.y // tile_size)
                    ex = {
                        "x": tile_x,
                        "y": tile_y,
                        "dest_map": str(_get_obj_prop(obj, "dest_map", "")),
                        "dest_x": int(_get_obj_prop(obj, "dest_x", 0)),
                        "dest_y": int(_get_obj_prop(obj, "dest_y", 0)),
                        "direction": str(_get_obj_prop(obj, "direction", "")),
                    }
                    exits.append(ex)

    # Derive logical tile IDs from GIDs
    tiles = _infer_tiles_from_gids(gids) if gids else []

    return {
        "id": map_id,
        "name": name,
        "width": width,
        "height": height,
        "tile_size": tile_size,
        "gids": gids,
        "tiles": tiles,
        "npcs": npcs,
        "exits": exits,
    }
