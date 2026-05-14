import arcade
from pyglet.window import key
from game.engine import register_scene
from game.text import create_text
from game.ui import COLORS


@register_scene("title")
class TitleScene:
    def __init__(self, engine):
        self.engine = engine
        self.timer = 0
        self.selection = 0
        self.options = ["NEW GAME", "LOAD GAME", "OPTIONS"]
        self.flash_timer = 0
        self._prev_scale = None
        self._texts = {}

    def update(self, delta_time):
        self.timer += delta_time
        self.flash_timer += delta_time

        inpt = self.engine.input
        if inpt.is_just_pressed(key.DOWN):
            self.selection = (self.selection + 1) % len(self.options)
        elif inpt.is_just_pressed(key.UP):
            self.selection = (self.selection - 1) % len(self.options)
        elif inpt.is_just_pressed(key.Z):
            self.select_option()

    def select_option(self):
        from game.save import has_save
        if self.selection == 0:
            self.engine.new_game()
            self.engine.set_scene("overworld")
        elif self.selection == 1:
            if has_save(0):
                from game.save import load_game
                data = load_game(0)
                self.engine.load_state(data["game_state"])
                self.engine.set_scene("overworld")
            else:
                self.selection = 0
                self.select_option()
        elif self.selection == 2:
            pass

    def _get_text(self, key, text, size, color, anchor_x="center"):
        scale = self.engine.get_scale()
        if self._prev_scale != scale or key not in self._texts:
            self._texts[key] = create_text(
                text, 0, 0,
                color, size,
                anchor_x=anchor_x, anchor_y="center"
            )
            self._prev_scale = scale
        return self._texts[key]

    def draw(self):
        scale = self.engine.get_scale()
        w, h = self.engine.get_size()
        arc_x = w // 2

        arcade.draw_lrbt_rectangle_filled(0, w, 0, h, arcade.color.BLACK)

        font_size = int(8 * scale)

        title_text = self._get_text("title", "FINAL FANTASY", font_size, COLORS["text"])
        title_text.x = arc_x
        title_text.y = h // 2 + 40 * scale - font_size
        title_text.draw()

        option_y = h // 2 - 20 * scale
        for i, option in enumerate(self.options):
            color = COLORS["cursor"] if i == self.selection else COLORS["text"]
            if i == self.selection and self.flash_timer % 1 < 0.5:
                color = (200, 200, 200)
            text = self._get_text(f"opt_{i}", option, font_size, color)
            text.x = arc_x
            text.y = option_y - i * 16 * scale - font_size
            text.draw()

        if self.flash_timer % 0.5 < 0.25:
            sel_x = arc_x - 50 * scale
            sel_y = (h // 2 - 20 * scale) - self.selection * 16 * scale
            sel_text = self._get_text("sel", ">", font_size, COLORS["text"])
            sel_text.x = sel_x
            sel_text.y = sel_y - font_size
            sel_text.draw()

        self._prev_scale = scale
