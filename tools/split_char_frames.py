#!/usr/bin/env python3
"""Split _all sprite entries in data/sprites.json into individual frame entries.

Each _all entry is a row of 6 frames: [dn_0, dn_1, rt_0, rt_1, up_0, up_1].
Each frame slot = 18px wide (16px content + 2px padding), 16px tall.
Left frames (lf_0, lf_1) are H-mirrors of rt_0, rt_1.
"""

import json
import os
import re
import sys

SPRITES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sprites.json")

FRAME_NAMES = ["dn_0", "dn_1", "rt_0", "rt_1", "up_0", "up_1"]
SLOT_WIDTH = 18  # 16px content + 2px padding
FRAME_W = 16
FRAME_H = 16


def main():
    with open(SPRITES_PATH, "r") as f:
        data = json.load(f)

    sprites = data["sprites"]

    # Collect keys to process (iterate over copy since we mutate)
    all_keys = list(sprites.keys())
    all_entries = {}
    for key in all_keys:
        if key.endswith("_all"):
            all_entries[key] = sprites[key]

    for all_key, entry in all_entries.items():
        # Derive character class prefix: e.g. "warrior_all" -> "warrior"
        char_class = all_key[: -len("_all")]
        sheet = entry["sheet"]
        base_x = entry["x"]
        base_y = entry["y"]

        # Remove the _all entry
        del sprites[all_key]

        # Add 6 frame entries
        for i, frame_name in enumerate(FRAME_NAMES):
            frame_key = f"{char_class}_{frame_name}"
            sprites[frame_key] = {
                "sheet": sheet,
                "x": base_x + i * SLOT_WIDTH,
                "y": base_y,
                "w": FRAME_W,
                "h": FRAME_H,
            }

        # Add mirrored left-frame entries (no x/y/w/h, just sheet + mirror_of)
        for src_name, dst_name in [("rt_0", "lf_0"), ("rt_1", "lf_1")]:
            src_key = f"{char_class}_{src_name}"
            dst_key = f"{char_class}_{dst_name}"
            sprites[dst_key] = {
                "sheet": sheet,
                "mirror_of": src_key,
            }

    with open(SPRITES_PATH, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"Done. Processed {len(all_entries)} _all entr{'y' if len(all_entries) == 1 else 'ies'}.")
    print(f"Total sprite entries: {len(sprites)}")


if __name__ == "__main__":
    main()
