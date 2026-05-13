#!/usr/bin/env python3
"""Sprite Picker Tool - View sprite sheets and pick sprite regions"""

import arcade
import os
import json
import sys

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRID_SIZE = 16


class SpritePicker(arcade.Window):
    def __init__(self):
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
        pan_speed = 20 / self.zoom
        if key == arcade.key.TAB:
            if modifiers & arcade.key.MOD_SHIFT:
                self.current_sheet_idx = (self.current_sheet_idx - 1) % len(self.sheet_names)
            else:
                self.current_sheet_idx = (self.current_sheet_idx + 1) % len(self.sheet_names)
            self._center_view()
        elif key == arcade.key.LEFT:
            self.pan_x -= pan_speed
        elif key == arcade.key.RIGHT:
            self.pan_x += pan_speed
        elif key == arcade.key.UP:
            self.pan_y += pan_speed
        elif key == arcade.key.DOWN:
            self.pan_y -= pan_speed
        elif key == arcade.key.RETURN:
            self._save_selection()
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

    def _save_selection(self):
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

        sheet = self.current_sheet
        if x1 < 0 or y1 < 0 or x2 > sheet.width or y2 > sheet.height:
            print(f"WARNING: Selection outside image bounds! Image is {sheet.width}x{sheet.height}")
            print(f"Your selection: x={x1} y={y1} w={w} h={h}")
            response = input("Save anyway? (y/n): ").strip().lower()
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

        output_path = os.path.join(os.path.dirname(__file__), "..", self.output_file)

        if os.path.exists(output_path):
            with open(output_path, "r") as f:
                data = json.load(f)
        else:
            data = {"sheets": {}, "sprites": {}}

        sprite_name = input("Enter sprite name (e.g., goblin): ").strip()
        if not sprite_name:
            print("No name entered")
            return

        data["sheets"][self.current_sheet_name] = self._get_sheet_filename(self.current_sheet_name)
        data["sprites"][sprite_name] = entry

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"Saved '{sprite_name}' to {output_path}")

    def _get_sheet_filename(self, sheet_name):
        if sheet_name == "enemies":
            return "Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Enemies & Bosses - Enemies.png"
        elif sheet_name == "characters":
            return "Game Boy _ GBC - Final Fantasy Legend 2 _ SaGa 2_ Hihou Densetsu - Characters - Characters.png"
        return sheet_name + ".png"

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
        sprite_list.draw()

        cx = self.width // 2 + self.pan_x * self.zoom
        cy = self.height // 2 + self.pan_y * self.zoom
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

        help_text = "Controls: Scroll=Zoom | Middle-drag=Pan | Left-drag=Select | Tab=Switch sheet | Enter=Save | R=Reset | 1/2/3/4=Zoom preset"
        arcade.draw_text(help_text, 10, 10, arcade.color.GRAY, 12)


if __name__ == "__main__":
    app = SpritePicker()
    arcade.run()