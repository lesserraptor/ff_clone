"""Export warrior sprite frames from the characters sheet as individual PNGs."""

import json
import os
import sys
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPRITES_PATH = PROJECT_ROOT / "data" / "sprites.json"
ASSETS_DIR = PROJECT_ROOT / "assets"
OUTPUT_DIR = PROJECT_ROOT  # project root

PREFIX = "warrior_"


def main() -> None:
    # 1. Load sprite definitions
    with open(SPRITES_PATH, "r") as f:
        data = json.load(f)

    sheets: dict[str, str] = data["sheets"]
    sprites: dict[str, dict] = data["sprites"]

    # 2. Resolve the characters sheet path
    chars_sheet_name = sheets["characters"]
    chars_path = ASSETS_DIR / chars_sheet_name
    if not chars_path.exists():
        print(f"ERROR: sheet not found: {chars_path}", file=sys.stderr)
        sys.exit(1)

    sheet_img = Image.open(chars_path).convert("RGBA")
    print(f"Loaded sheet: {chars_path}  ({sheet_img.size})")

    # 3. Filter warrior_* sprites
    warrior_defs = {name: defn for name, defn in sprites.items() if name.startswith(PREFIX)}

    if not warrior_defs:
        print(f"No sprites found with prefix '{PREFIX}'")
        sys.exit(0)

    # 4. Export each frame
    for name, defn in warrior_defs.items():
        out_path = OUTPUT_DIR / f"{name}.png"

        if "mirror_of" in defn:
            # Mirror: flip source horizontally
            src_name = defn["mirror_of"]
            src_defn = sprites.get(src_name)
            if src_defn is None:
                print(f"  SKIP  {name}: mirror_of '{src_name}' not found in sprites.json")
                continue
            if "x" not in src_defn or "y" not in src_defn or "w" not in src_defn or "h" not in src_defn:
                print(f"  SKIP  {name}: source '{src_name}' has no rect (mirror_of chain?)")
                continue
            region = sheet_img.crop(
                (src_defn["x"], src_defn["y"],
                 src_defn["x"] + src_defn["w"],
                 src_defn["y"] + src_defn["h"])
            )
            flipped = region.transpose(Image.FLIP_LEFT_RIGHT)
            flipped.save(out_path)
            print(f"  MIRROR {src_name} -> {name}  ->  {out_path.name}  ({flipped.size})")

        elif "x" in defn and "y" in defn and "w" in defn and "h" in defn:
            # Direct crop
            region = sheet_img.crop(
                (defn["x"], defn["y"],
                 defn["x"] + defn["w"],
                 defn["y"] + defn["h"])
            )
            region.save(out_path)
            print(f"  CROP   {name}  ->  {out_path.name}  ({region.size})")

        else:
            print(f"  SKIP   {name}: no rect and no mirror_of")

    print("\nDone.")


if __name__ == "__main__":
    main()
