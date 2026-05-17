"""Convert old tile_id map format to GID-based format with tree expansion."""

import json
import os
import sys
from PIL import Image

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
MAPS_PATH = os.path.join(DATA_DIR, "maps.json")
OUT_PATH = os.path.join(DATA_DIR, "maps_converted.json")
TILESET_PATH = os.path.join(ASSETS_DIR, "extracted_hometown_tileset_rgb.png")

# Tile-ID to GID mapping for non-tree tiles
TILE_TO_GID = {
    0: 3,   # Grass -> sky/clouds
    1: 15,  # Water -> solid gray
    3: 66,  # Path -> solid ground
    4: 5,   # Floor -> brick floor
    5: 7,   # Wall -> detailed wall
    6: 16,  # Door -> doorway
    7: 3,   # Sand -> same as grass
    8: 8,   # Mountain -> dark trim
    9: 12,  # Bridge -> vertical stone
}

def convert_overworld(tiles, width, height):
    """Convert overworld map tiles to GIDs with tree expansion."""
    gids = [[0 for _ in range(width)] for _ in range(height)]
    
    # Pass 1: assign GIDs based on tile type and position
    for y in range(height):
        for x in range(width):
            tile = tiles[y][x]
            
            # Left and right borders always GID 1
            if x == 0 or x == width - 1:
                if tile == 2 or tile == 0:
                    gids[y][x] = 1  # Forest bg border
                else:
                    gids[y][x] = TILE_TO_GID.get(tile, 0)
                continue
            
            non_tree_gid = TILE_TO_GID.get(tile)
            if non_tree_gid is not None:
                gids[y][x] = non_tree_gid
                continue
            
            # Tree (tile_id=2) handling
            if tile == 2:
                if y == 0:
                    # Top border -> GID 1
                    gids[y][x] = 1
                elif y == height - 1:
                    # Bottom row -> GID 9 except corners (already handled above)
                    gids[y][x] = 9
                elif y > 0 and tiles[y-1][x] == 2:
                    # Tree above -> trunk
                    gids[y][x] = 2
                else:
                    # Tree top -> canopy
                    gids[y][x] = 9
            else:
                gids[y][x] = tile  # fallback
    
    # Pass 2: ensure trunks below canopies
    for y in range(height - 1):
        for x in range(width):
            # Skip left/right borders - they stay GID 1
            if x == 0 or x == width - 1:
                continue
            # Top border (GID 1 at row 0): set below to trunk
            if y == 0 and gids[y][x] == 1:
                gids[y+1][x] = 2
            # Interior canopy (GID 9): ensure below is trunk
            elif gids[y][x] == 9:
                below = gids[y+1][x]
                if below not in (1, 2):  # Don't override borders
                    gids[y+1][x] = 2
    
    return gids


def convert_normal(tiles, width, height):
    """Simple 1:1 conversion for non-overworld maps (town, dungeon)."""
    gids = [[0 for _ in range(width)] for _ in range(height)]
    for y in range(height):
        for x in range(width):
            gid = TILE_TO_GID.get(tiles[y][x])
            gids[y][x] = gid if gid is not None else tiles[y][x]
    return gids


def main():
    with open(MAPS_PATH, "r") as f:
        data = json.load(f)
    
    OVERWORLD_IDS = {"overworld_1", "overworld_2", "overworld_3"}
    
    for map_id, map_data in data["maps"].items():
        tiles = map_data["tiles"]
        h = len(tiles)
        w = len(tiles[0]) if h > 0 else 0
        
        if map_id in OVERWORLD_IDS:
            gids = convert_overworld(tiles, w, h)
        else:
            gids = convert_normal(tiles, w, h)
        
        map_data["gids"] = gids
    
    # Add lookup table
    data["gid_lookup"] = {str(k): v for k, v in TILE_TO_GID.items()}
    data["gid_lookup"]["2_tree_canopy_border"] = 1
    data["gid_lookup"]["2_tree_canopy_center"] = 9
    data["gid_lookup"]["2_tree_trunk"] = 2
    
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved GID data to {OUT_PATH}")
    
    # Generate preview
    generate_preview(data["maps"]["overworld_1"])


def generate_preview(map_data):
    """Generate PNG preview of converted map using tileset."""
    tileset = Image.open(TILESET_PATH).convert("RGBA")
    tw, th = 16, 16  # tile size
    cols_tileset = tileset.width // tw  # 10
    
    gids = map_data["gids"]
    h = len(gids)
    w = len(gids[0])
    scale = 4
    out_w = w * tw * scale
    out_h = h * th * scale + 30  # extra space for label
    
    img = Image.new("RGBA", (out_w, out_h), (50, 50, 50, 255))
    
    for y in range(h):
        for x in range(w):
            gid = gids[y][x]
            if gid <= 0:
                continue
            # GID is 1-based, position in tileset grid (10 cols)
            sx = ((gid - 1) % cols_tileset) * tw
            sy = ((gid - 1) // cols_tileset) * th
            tile_img = tileset.crop((sx, sy, sx + tw, sy + th))
            # Scale up
            tile_img = tile_img.resize((tw * scale, th * scale), Image.NEAREST)
            px = x * tw * scale
            py = y * th * scale + 30
            img.paste(tile_img, (px, py))
    
    # Add label at top
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        font = ImageFont.load_default()
    draw.text((10, 4), "Converted: overworld_1", (255, 255, 255), font=font)
    
    out_path = os.path.join(ASSETS_DIR, "preview_converted.png")
    img.save(out_path)
    print(f"Saved preview to {out_path}")


if __name__ == "__main__":
    main()
