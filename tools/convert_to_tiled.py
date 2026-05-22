"""Convert maps_converted.json to Tiled .tmx + .tsj format.

Produces:
  assets/hometown_tileset.tsj    — JSON tileset referencing the PNG
  assets/maps/<map_id>.tmx       — Tiled XML map per map (CSV tile layer + object layers)
"""

import json
import os
import xml.etree.ElementTree as ET

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
MAPS_DIR = os.path.join(ASSETS_DIR, "maps")

CONVERTED_PATH = os.path.join(DATA_DIR, "maps_converted.json")
TILESET_PATH = "extracted_hometown_tileset_rgb.png"
TSJ_PATH = os.path.join(ASSETS_DIR, "hometown_tileset.tsj")

TILE_W = 16
TILE_H = 16
COLS = 10
ROWS = 9
TILE_COUNT = COLS * ROWS

# Which GIDs are walkable (based on tile_defs in maps.json)
# GID 1-based, tile IDs from original map data
GID_WALKABLE = {
    1: False,   # tree_canopy_border
    2: False,   # tree_trunk
    3: True,    # grass / sand
    5: True,    # floor
    7: False,   # wall
    8: False,   # mountain
    9: False,   # tree_canopy_center
    12: True,   # bridge / vertical stone
    15: True,   # water / solid gray
    16: True,   # door / doorway
    66: True,   # path / solid ground
}


def _build_tileset_json():
    """Build the .tsj JSON tileset dict."""
    tiles_array = []
    for gid in range(1, TILE_COUNT + 1):
        tile_id = gid - 1  # 0-based in tileset
        walkable = GID_WALKABLE.get(gid, True)
        tile_entry = {
            "id": tile_id,
            "properties": [
                {"name": "walkable", "type": "bool", "value": walkable},
            ],
        }
        tiles_array.append(tile_entry)

    return {
        "columns": COLS,
        "image": TILESET_PATH,
        "imageheight": ROWS * TILE_H,
        "imagewidth": COLS * TILE_W,
        "margin": 0,
        "name": "hometown_tileset",
        "spacing": 0,
        "tilecount": TILE_COUNT,
        "tiledversion": "1.11",
        "tileheight": TILE_H,
        "tilewidth": TILE_W,
        "tiles": tiles_array,
    }


def _make_csv_data(gids):
    """Convert 2D GID grid to single-line CSV string.

    pytiled_parser splits data_element.text by ',' and calls int(v.strip()).
    Multi-line CSV produces tokens like '1\\n1' which int() rejects.
    Single-line comma-separated values work correctly.
    """
    return ",".join(str(g) for row in gids for g in row)


def _build_tmx(map_id, map_data):
    """Build an xml.etree.ElementTree for a .tmx map."""
    width = map_data["width"]
    height = map_data["height"]
    gids = map_data["gids"]
    npcs = map_data.get("npcs", [])
    exits = map_data.get("exits", [])
    map_name = map_data.get("name", map_id)

    total_objects = len(npcs) + len(exits)
    next_layer_id = 4  # tile + NPCs + Exits = 3 layers
    next_object_id = total_objects + 1

    root = ET.Element("map", {
        "version": "1.10",
        "tiledversion": "1.11",
        "orientation": "orthogonal",
        "renderorder": "right-down",
        "width": str(width),
        "height": str(height),
        "tilewidth": str(TILE_W),
        "tileheight": str(TILE_H),
        "infinite": "0",
        "nextlayerid": str(next_layer_id),
        "nextobjectid": str(next_object_id),
    })

    # Map-level custom properties
    props = ET.SubElement(root, "properties")
    ET.SubElement(props, "property", {"name": "name", "type": "string", "value": map_name})

    # Tileset reference
    ET.SubElement(root, "tileset", {"firstgid": "1", "source": "../hometown_tileset.tsj"})

    # Tile layer
    layer_el = ET.SubElement(root, "layer", {
        "id": "1",
        "name": "Tile Layer 1",
        "width": str(width),
        "height": str(height),
    })
    data_el = ET.SubElement(layer_el, "data", {"encoding": "csv"})
    data_el.text = _make_csv_data(gids)

    # NPCs object layer
    if npcs:
        obj_group = ET.SubElement(root, "objectgroup", {
            "id": "2",
            "name": "NPCs",
        })
        for idx, npc in enumerate(npcs):
            obj_el = ET.SubElement(obj_group, "object", {
                "id": str(idx + 1),
                "x": str(npc["x"] * TILE_W),
                "y": str(npc["y"] * TILE_H),
            })
            # Custom properties
            oprops = ET.SubElement(obj_el, "properties")
            if "name" in npc:
                ET.SubElement(oprops, "property", {
                    "name": "name", "type": "string", "value": npc["name"],
                })
            if "script" in npc:
                ET.SubElement(oprops, "property", {
                    "name": "script_id", "type": "string", "value": npc["script"],
                })
            ET.SubElement(obj_el, "point")

    # Exits object layer
    if exits:
        obj_group = ET.SubElement(root, "objectgroup", {
            "id": "3",
            "name": "Exits",
        })
        for idx, ex in enumerate(exits, start=len(npcs) + 1):
            obj_el = ET.SubElement(obj_group, "object", {
                "id": str(idx),
                "x": str(ex["x"] * TILE_W),
                "y": str(ex["y"] * TILE_H),
            })
            oprops = ET.SubElement(obj_el, "properties")
            ET.SubElement(oprops, "property", {
                "name": "dest_map", "type": "string", "value": str(ex.get("dest_map", "")),
            })
            ET.SubElement(oprops, "property", {
                "name": "dest_x", "type": "int", "value": str(ex.get("dest_x", 0)),
            })
            ET.SubElement(oprops, "property", {
                "name": "dest_y", "type": "int", "value": str(ex.get("dest_y", 0)),
            })
            ET.SubElement(oprops, "property", {
                "name": "direction", "type": "string", "value": str(ex.get("direction", "")),
            })
            ET.SubElement(obj_el, "point")

    return root


def _indent_xml(elem, level=0):
    """Add whitespace indentation to an ElementTree for pretty output."""
    indent = "  "
    children = list(elem)
    if not children:
        return
    if elem.text and not elem.text.strip():
        elem.text = "\n" + indent * (level + 1)
    for child in children:
        _indent_xml(child, level + 1)
    if elem.tail and not elem.tail.strip():
        elem.tail = "\n" + indent * level
    if not elem.text or not elem.text.strip():
        elem.text = "\n" + indent * (level + 1)
    # Add newline before closing tag if has children
    if children:
        last = children[-1]
        if last.tail and not last.tail.strip():
            last.tail = "\n" + indent * level


def main():
    with open(CONVERTED_PATH, "r") as f:
        data = json.load(f)

    os.makedirs(MAPS_DIR, exist_ok=True)

    # Write tileset .tsj
    tsj_data = _build_tileset_json()
    with open(TSJ_PATH, "w") as f:
        json.dump(tsj_data, f, indent=2)
    print(f"Wrote tileset: {TSJ_PATH}")

    # Write each map as .tmx
    for map_id, map_data in data.get("maps", {}).items():
        root = _build_tmx(map_id, map_data)
        _indent_xml(root)
        tree = ET.ElementTree(root)
        tmx_path = os.path.join(MAPS_DIR, f"{map_id}.tmx")
        tree.write(tmx_path, xml_declaration=True, encoding="UTF-8")
        print(f"Wrote map: {tmx_path} ({map_data['width']}x{map_data['height']}, "
              f"{len(map_data.get('npcs', []))} NPCs, "
              f"{len(map_data.get('exits', []))} exits)")

    print(f"\nDone. {len(data.get('maps', {}))} maps converted to Tiled format in {MAPS_DIR}/")


if __name__ == "__main__":
    main()
