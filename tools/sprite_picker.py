#!/usr/bin/env python3
"""Sprite Picker Tool - View sprite sheets and pick sprite regions"""

from PIL import Image, ImageDraw

import io

import arcade
import os
import json
import sys
import argparse

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRID_SIZE = 16

QUEUE_COLORS = [
    (0, 255, 0, 120),      # green
    (0, 255, 255, 120),    # cyan
    (255, 255, 0, 120),    # yellow
    (255, 0, 255, 120),    # magenta
    (255, 165, 0, 120),    # orange
]


class SpritePicker(arcade.Window):
    def __init__(self, class_name=None):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, "Sprite Picker", resizable=True)
        arcade.set_background_color((20, 20, 20))

        self.sheets = {}
        self.sheet_names = []
        self.current_sheet_idx = 0

        self.zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 20.0

        self.pan_x = 0
        self.pan_y = 0

        self.selecting = False
        self.select_start = None
        self.select_end = None

        self.panning = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.output_file = "data/sprites.json"
        self.selection_queue = []
        self.show_grid = False
        self.grid_size = 16
        self.grid_overlay_texture = None
        self.held_keys = {}
        self.shift_held = False

        self.guided_class_name = class_name
        self.guided_active = class_name is not None
        self.guided_frame_names = ["dn_0", "dn_1", "rt_0", "rt_1", "up_0", "up_1"]
        self.guided_frame_idx = 0
        self.guided_prompt_text = None

        self._load_sheets()

    def _get_assets_path(self):
        return os.path.join(os.path.dirname(__file__), "..", "assets")

    def _load_sheets(self):
        assets_path = self._get_assets_path()

        enemy_sheet = "Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Enemies & Bosses - Enemies.png"
        char_sheet = "Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Characters - Characters.png"

        if os.path.exists(os.path.join(assets_path, enemy_sheet)):
            self.sheets["enemies"] = arcade.load_texture(os.path.join(assets_path, enemy_sheet))
            self.sheet_names.append("enemies")

        if os.path.exists(os.path.join(assets_path, char_sheet)):
            self.sheets["characters"] = arcade.load_texture(os.path.join(assets_path, char_sheet))
            self.sheet_names.append("characters")

        self.current_sheet_idx = 0
        self.grid_overlay_texture = None
        self._center_view()

    def _center_view(self):
        if not self.sheet_names:
            return
        sheet = self.sheets[self.sheet_names[self.current_sheet_idx]]
        self.pan_x = -sheet.width // 2
        self.pan_y = -sheet.height // 2

    @property
    def current_sheet(self):
        if not self.sheet_names:
            return None
        return self.sheets[self.sheet_names[self.current_sheet_idx]]

    @property
    def current_sheet_name(self):
        if not self.sheet_names:
            return ""
        return self.sheet_names[self.current_sheet_idx]

    def _screen_to_image(self, screen_x, screen_y):
        cx = self.width // 2 + self.pan_x * self.zoom
        cy = self.height // 2 + self.pan_y * self.zoom
        sheet = self.current_sheet
        img_x = int((screen_x - cx) / self.zoom + sheet.width / 2)
        img_y = int((cy - screen_y) / self.zoom + sheet.height / 2)
        return img_x, img_y

    def on_resize(self, width, height):
        super().on_resize(width, height)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_MIDDLE:
            self.panning = True
            self.last_mouse_x = x
            self.last_mouse_y = y
        elif button == arcade.MOUSE_BUTTON_LEFT:
            img_x, img_y = self._screen_to_image(x, y)
            self.selecting = True
            self.select_start = (img_x, img_y)
            self.select_end = (img_x, img_y)

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_MIDDLE:
            self.panning = False
        elif button == arcade.MOUSE_BUTTON_LEFT:
            self.selecting = False

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & arcade.MOUSE_BUTTON_MIDDLE:
            self.pan_x += dx / self.zoom
            self.pan_y += dy / self.zoom
        elif buttons & arcade.MOUSE_BUTTON_LEFT:
            img_x, img_y = self._screen_to_image(x, y)
            self.select_end = (img_x, img_y)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if scroll_y > 0 or scroll_x > 0:
            self.zoom = min(self.zoom * 1.2, self.max_zoom)
        else:
            self.zoom = max(self.zoom / 1.2, self.min_zoom)

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.LSHIFT, arcade.key.RSHIFT):
            self.shift_held = True
            return

        if key in (arcade.key.LEFT, arcade.key.RIGHT, arcade.key.UP, arcade.key.DOWN):
            if key not in self.held_keys:
                self.held_keys[key] = 0.05  # fire on first on_update frame
            return

        elif key == arcade.key.F:
            if self.guided_class_name:
                self.guided_active = not self.guided_active
                if self.guided_active:
                    self.guided_frame_idx = 0
                    self.select_start = None
                    self.select_end = None
                    name = self.guided_frame_names[0]
                    print(f"GUIDED MODE: Select {self.guided_class_name}_{name}")
                else:
                    print("Guided mode deactivated")
        elif key == arcade.key.TAB:
            if modifiers & arcade.key.MOD_SHIFT:
                self.current_sheet_idx = (self.current_sheet_idx - 1) % len(self.sheet_names)
            else:
                self.current_sheet_idx = (self.current_sheet_idx + 1) % len(self.sheet_names)
            self._center_view()

        elif key == arcade.key.RETURN:
            if self.guided_active:
                self._guided_save_and_advance()
            else:
                self._queue_selection()
        elif key == arcade.key.S:
            if self.guided_active:
                return
            self._save_all_queued()
        elif key == arcade.key.ESCAPE:
            self.select_start = None
            self.select_end = None
            # In guided mode, Esc just clears selection, doesn't exit guided
        elif key == arcade.key.G:
            self.show_grid = not self.show_grid
            print(f"Grid {'on' if self.show_grid else 'off'}")
        elif key == arcade.key.R:
            self._center_view()
        elif key == arcade.key.NUM_1:
            self.zoom = 1.0
        elif key == arcade.key.NUM_2:
            self.zoom = 2.0
        elif key == arcade.key.NUM_3:
            self.zoom = 4.0
        elif key == arcade.key.NUM_4:
            self.zoom = 8.0

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LSHIFT, arcade.key.RSHIFT):
            self.shift_held = False
        else:
            self.held_keys.pop(key, None)

    def on_update(self, delta_time):
        repeat_interval = 0.05  # 20Hz repeat
        for key in list(self.held_keys.keys()):
            self.held_keys[key] += delta_time
            if self.held_keys[key] >= repeat_interval:
                self.held_keys[key] -= repeat_interval
                self._process_arrow(key)

    def _process_arrow(self, key):
        pan_speed = 20 / self.zoom

        if key == arcade.key.LEFT:
            if self.select_start and self.select_end:
                if self.shift_held:
                    dx = -1
                    self.select_start = (self.select_start[0] + dx, self.select_start[1])
                    self.select_end = (self.select_end[0] + dx, self.select_end[1])
                else:
                    self.select_end = (self.select_end[0] - 1, self.select_end[1])
                self._normalize_selection()
            else:
                self.pan_x -= pan_speed

        elif key == arcade.key.RIGHT:
            if self.select_start and self.select_end:
                if self.shift_held:
                    dx = 1
                    self.select_start = (self.select_start[0] + dx, self.select_start[1])
                    self.select_end = (self.select_end[0] + dx, self.select_end[1])
                else:
                    self.select_end = (self.select_end[0] + 1, self.select_end[1])
                self._normalize_selection()
            else:
                self.pan_x += pan_speed

        elif key == arcade.key.UP:
            if self.select_start and self.select_end:
                if self.shift_held:
                    dy = -1
                    self.select_start = (self.select_start[0], self.select_start[1] + dy)
                    self.select_end = (self.select_end[0], self.select_end[1] + dy)
                else:
                    # Image y decreases going up -> shorter
                    self.select_end = (self.select_end[0], self.select_end[1] - 1)
                self._normalize_selection()
            else:
                self.pan_y += pan_speed

        elif key == arcade.key.DOWN:
            if self.select_start and self.select_end:
                if self.shift_held:
                    dy = 1
                    self.select_start = (self.select_start[0], self.select_start[1] + dy)
                    self.select_end = (self.select_end[0], self.select_end[1] + dy)
                else:
                    # Image y increases going down -> taller
                    self.select_end = (self.select_end[0], self.select_end[1] + 1)
                self._normalize_selection()
            else:
                self.pan_y -= pan_speed

    def _normalize_selection(self):
        if not self.select_start or not self.select_end:
            return
        x1 = min(self.select_start[0], self.select_end[0])
        y1 = min(self.select_start[1], self.select_end[1])
        x2 = max(self.select_start[0], self.select_end[0])
        y2 = max(self.select_start[1], self.select_end[1])
        if x2 - x1 < 1:
            x2 = x1 + 1
        if y2 - y1 < 1:
            y2 = y1 + 1
        self.select_start = (x1, y1)
        self.select_end = (x2, y2)

    def _queue_selection(self):
        if not self.select_start or not self.select_end:
            print("No selection to queue")
            return

        x1 = min(self.select_start[0], self.select_end[0])
        y1 = min(self.select_start[1], self.select_end[1])
        x2 = max(self.select_start[0], self.select_end[0])
        y2 = max(self.select_start[1], self.select_end[1])

        w = x2 - x1
        h = y2 - y1

        if w <= 0 or h <= 0:
            print("Invalid selection")
            return

        sheet = self.current_sheet
        if x1 < 0 or y1 < 0 or x2 > sheet.width or y2 > sheet.height:
            print(f"WARNING: Selection outside image bounds! Image is {sheet.width}x{sheet.height}")
            print(f"Your selection: x={x1} y={y1} w={w} h={h}")
            response = input("Queue anyway? (y/n): ").strip().lower()
            if response != 'y':
                print("Selection cancelled")
                return

        entry = {
            "sheet": self.current_sheet_name,
            "x": x1,
            "y": y1,
            "w": w,
            "h": h
        }

        print(f"Selection: {entry}")

        sprite_name = input("Enter sprite name (e.g., goblin): ").strip()
        if not sprite_name:
            print("No name entered")
            return

        self.selection_queue.append({"name": sprite_name, "entry": entry})
        print(f"Queued '{sprite_name}' ({len(self.selection_queue)} total)")

    def _save_all_queued(self):
        if not self.selection_queue:
            print("Nothing to save")
            return

        output_path = os.path.join(os.path.dirname(__file__), "..", self.output_file)

        if os.path.exists(output_path):
            with open(output_path, "r") as f:
                data = json.load(f)
        else:
            data = {"sheets": {}, "sprites": {}}

        names = []
        for item in self.selection_queue:
            name = item["name"]
            entry = item["entry"]
            data["sheets"][entry["sheet"]] = self._get_sheet_filename(entry["sheet"])
            data["sprites"][name] = entry
            names.append(name)

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"Saved {len(names)} sprites: {', '.join(names)}")
        self.selection_queue.clear()

    def _guided_save_and_advance(self):
        if not self.select_start or not self.select_end:
            print("No selection to save")
            return

        x1 = min(self.select_start[0], self.select_end[0])
        y1 = min(self.select_start[1], self.select_end[1])
        x2 = max(self.select_start[0], self.select_end[0])
        y2 = max(self.select_start[1], self.select_end[1])

        w = x2 - x1
        h = y2 - y1

        if w <= 0 or h <= 0:
            print("Invalid selection")
            return

        frame_name = self.guided_frame_names[self.guided_frame_idx]
        sprite_id = f"{self.guided_class_name}_{frame_name}"

        # Read current sprites.json
        json_path = os.path.join(os.path.dirname(__file__), "..", "data", "sprites.json")
        if os.path.exists(json_path):
            with open(json_path) as f:
                data = json.load(f)
        else:
            data = {"sheets": {}, "sprites": {}}

        # Ensure the sheet entry exists
        data["sheets"][self.current_sheet_name] = self._get_sheet_filename(self.current_sheet_name)

        # Add the sprite entry
        data["sprites"][sprite_id] = {
            "sheet": self.current_sheet_name,
            "x": x1,
            "y": y1,
            "w": w,
            "h": h,
        }

        # Write back
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

        entry = data["sprites"][sprite_id]
        print(f"✅ Saved {sprite_id}: x={entry['x']} y={entry['y']} w={entry['w']} h={entry['h']}")

        # Advance
        self.guided_frame_idx += 1

        if self.guided_frame_idx >= len(self.guided_frame_names):
            # All 6 frames done! Add mirror entries
            for src, dst in [("rt_0", "lf_0"), ("rt_1", "lf_1")]:
                data["sprites"][f"{self.guided_class_name}_{dst}"] = {
                    "sheet": self.current_sheet_name,
                    "mirror_of": f"{self.guided_class_name}_{src}",
                }
            with open(json_path, "w") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
            print(f"✅ All frames saved for {self.guided_class_name}! Added mirrored frames.")
            self.guided_active = False
        else:
            next_name = self.guided_frame_names[self.guided_frame_idx]
            print(f"👉 Next: {self.guided_class_name}_{next_name}")

        self.select_start = None
        self.select_end = None

    def _get_sheet_filename(self, sheet_name):
        if sheet_name == "enemies":
            return "Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Enemies & Bosses - Enemies.png"
        elif sheet_name == "characters":
            return "Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Characters - Characters.png"
        return sheet_name + ".png"

    def _build_grid_texture(self):
        sheet = self.current_sheet
        if not sheet:
            return
        w, h = sheet.width, sheet.height
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        color = (100, 100, 100, 120)
        # Vertical lines at each pixel border
        for gx in range(1, w):
            draw.line([(gx, 0), (gx, h)], fill=color, width=1)
        # Horizontal lines at each pixel border
        for gy in range(1, h):
            draw.line([(0, gy), (w, gy)], fill=color, width=1)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        self.grid_overlay_texture = arcade.load_texture(buf)

    def _draw_grid(self):
        if not self.current_sheet or not self.show_grid:
            return
        if self.zoom < 2.0:
            return
        if not self.grid_overlay_texture:
            self._build_grid_texture()
            if not self.grid_overlay_texture:
                return

        cx = self.width // 2 + self.pan_x * self.zoom
        cy = self.height // 2 + self.pan_y * self.zoom

        sprite = arcade.Sprite()
        sprite.texture = self.grid_overlay_texture
        sprite.center_x = cx
        sprite.center_y = cy
        sprite.scale = self.zoom
        sl = arcade.SpriteList()
        sl.append(sprite)
        sl.draw(pixelated=True)

    def _draw_queued_selections(self):
        if not self.selection_queue:
            return
        sheet = self.current_sheet
        if not sheet:
            return
        sheet_name = self.current_sheet_name

        cx = self.width // 2 + self.pan_x * self.zoom
        cy = self.height // 2 + self.pan_y * self.zoom

        queued = [q for q in self.selection_queue if q["entry"]["sheet"] == sheet_name]
        if not queued:
            return

        for i, item in enumerate(queued):
            entry = item["entry"]
            color = QUEUE_COLORS[i % len(QUEUE_COLORS)]

            x1 = entry["x"]
            y1 = entry["y"]
            x2 = entry["x"] + entry["w"]
            y2 = entry["y"] + entry["h"]

            screen_x1 = cx + (x1 - sheet.width / 2) * self.zoom
            screen_x2 = cx + (x2 - sheet.width / 2) * self.zoom
            screen_y2 = cy + (sheet.height / 2 - y1) * self.zoom
            screen_y1 = cy + (sheet.height / 2 - y2) * self.zoom

            arcade.draw_lrbt_rectangle_filled(screen_x1, screen_x2, screen_y1, screen_y2, color)
            arcade.draw_lrbt_rectangle_outline(screen_x1, screen_x2, screen_y1, screen_y2, arcade.color.WHITE, 1)

            if self.zoom >= 2.0:
                arcade.draw_text(item["name"], screen_x1, screen_y1 + 2, arcade.color.WHITE, 10)

    def on_draw(self):
        self.clear()

        if not self.current_sheet:
            return

        cx = self.width // 2 + self.pan_x * self.zoom
        cy = self.height // 2 + self.pan_y * self.zoom

        sprite_list = arcade.SpriteList()
        sprite = arcade.Sprite()
        sprite.texture = self.current_sheet
        sprite.center_x = cx
        sprite.center_y = cy
        sprite.scale = self.zoom
        sprite_list.append(sprite)
        sprite_list.draw(pixelated=True)

        cx = self.width // 2 + self.pan_x * self.zoom
        cy = self.height // 2 + self.pan_y * self.zoom

        self._draw_grid()

        size = 20
        arcade.draw_lrbt_rectangle_outline(cx - size, cx + size, cy - 2, cy + 2, arcade.color.RED, 1)
        arcade.draw_lrbt_rectangle_outline(cx - 2, cx + 2, cy - size, cy + size, arcade.color.RED, 1)

        if self.select_start and self.select_end:
            x1 = min(self.select_start[0], self.select_end[0])
            y1 = min(self.select_start[1], self.select_end[1])
            x2 = max(self.select_start[0], self.select_end[0])
            y2 = max(self.select_start[1], self.select_end[1])

            cx = self.width // 2 + self.pan_x * self.zoom
            cy = self.height // 2 + self.pan_y * self.zoom
            sheet = self.current_sheet

            screen_x1 = cx + (x1 - sheet.width / 2) * self.zoom
            screen_x2 = cx + (x2 - sheet.width / 2) * self.zoom
            screen_y2 = cy + (sheet.height / 2 - y1) * self.zoom
            screen_y1 = cy + (sheet.height / 2 - y2) * self.zoom

            w = screen_x2 - screen_x1
            h = screen_y2 - screen_y1

            arcade.draw_lrbt_rectangle_outline(
                screen_x1, screen_x2, screen_y1, screen_y2, arcade.color.YELLOW, 2
            )

        self._draw_queued_selections()

        mouse_img_x, mouse_img_y = self._screen_to_image(self.mouse["x"], self.mouse["y"])

        info_text = f"Sheet: {self.current_sheet_name} ({self.current_sheet.width}x{self.current_sheet.height})"
        arcade.draw_text(info_text, 10, self.height - 20, arcade.color.WHITE, 14)

        zoom_text = f"Zoom: {self.zoom:.1f}x  Pan: ({self.pan_x:.0f}, {self.pan_y:.0f})"
        arcade.draw_text(zoom_text, 10, self.height - 40, arcade.color.WHITE, 14)

        coord_text = f"Mouse: ({mouse_img_x}, {mouse_img_y})"
        arcade.draw_text(coord_text, 10, self.height - 60, arcade.color.WHITE, 14)

        if self.select_start and self.select_end:
            x1 = min(self.select_start[0], self.select_end[0])
            y1 = min(self.select_start[1], self.select_end[1])
            x2 = max(self.select_start[0], self.select_end[0])
            y2 = max(self.select_start[1], self.select_end[1])
            sel_text = f"Selection: x={x1} y={y1} w={x2-x1} h={y2-y1}"
            arcade.draw_text(sel_text, 10, self.height - 80, arcade.color.YELLOW, 14)

        # Queue + grid status
        y = 10
        queue_str = f"Queue: {len(self.selection_queue)}"
        if self.selection_queue:
            names = [item["name"] for item in self.selection_queue[:5]]
            if len(self.selection_queue) > 5:
                names.append("...")
            queue_str += " [" + ", ".join(names) + "]"
        grid_str = f"Grid: {'ON' if self.show_grid else 'OFF'}"
        arcade.draw_text(f"{queue_str} | {grid_str}", 10, y, arcade.color.CYAN, 12)
        y += 16

        help_lines = [
            "Scroll=Zoom | MMB-drag=Pan | LMB-drag=Select",
            "Enter=Queue | S=Save all | Esc=Clear sel | G=Grid",
            "Tab=Sheet | Arrows=Resize | Shift+Arrows=Move",
            "R=Reset | 1/2/3/4=Zoom preset",
        ]
        if self.guided_class_name:
            help_lines.append(f"F=Toggle guided mode | Guided: {'ON' if self.guided_active else 'OFF'}")
        for line in help_lines:
            arcade.draw_text(line, 10, y, arcade.color.GRAY, 12)
            y += 16

        if self.guided_active:
            frame_name = self.guided_frame_names[self.guided_frame_idx]
            prompt = f"FRAME {self.guided_frame_idx+1}/{len(self.guided_frame_names)}: {self.guided_class_name}_{frame_name}"
            arcade.draw_text(prompt,
                10, self.height - 20,
                arcade.color.YELLOW, 12,
                bold=True)
            arcade.draw_text("Draw selection, press Enter to confirm, Esc to cancel",
                10, self.height - 35,
                arcade.color.LIGHT_GRAY, 9)


def main():
    parser = argparse.ArgumentParser(description="Sprite picker tool")
    parser.add_argument("--class", dest="class_name", default=None,
                        help="Character class for guided frame mode (e.g., warrior)")
    args = parser.parse_args()
    app = SpritePicker(class_name=args.class_name)
    arcade.run()


if __name__ == "__main__":
    main()
