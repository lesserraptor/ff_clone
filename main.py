import arcade

BASE_WIDTH = 240
BASE_HEIGHT = 160
SCALE_MIN = 1
SCALE_MAX = 5

SCREEN_TITLE = "Final Fantasy"
WINDOW_WIDTH = BASE_WIDTH * 3
WINDOW_HEIGHT = BASE_HEIGHT * 3


class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(
            WINDOW_WIDTH,
            WINDOW_HEIGHT,
            SCREEN_TITLE,
            resizable=True,
            center_window=True,
        )
        self.scale_factor = 3
        self.game = None
        self.pressed_keys = set()

    def set_scale(self, scale):
        self.scale_factor = max(SCALE_MIN, min(SCALE_MAX, scale))
        self.set_size(BASE_WIDTH * self.scale_factor, BASE_HEIGHT * self.scale_factor)

    def on_key_press(self, symbol, modifiers):
        self.pressed_keys.add(symbol)
        if symbol == arcade.key.MINUS and self.scale_factor > SCALE_MIN:
            self.set_scale(self.scale_factor - 1)
        elif symbol == arcade.key.EQUAL and self.scale_factor < SCALE_MAX:
            self.set_scale(self.scale_factor + 1)

    def on_key_release(self, symbol, modifiers):
        self.pressed_keys.discard(symbol)

    def setup(self):
        from game.engine import GameEngine
        import game.scenes.title
        import game.scenes.overworld
        import game.scenes.battle
        import game.scenes.menu
        self.game = GameEngine(self)
        self.game.set_scene("title")

    def on_update(self, delta_time):
        if self.game:
            self.game.update(delta_time)

    def on_draw(self):
        self.clear()
        if self.game:
            self.game.draw()


if __name__ == "__main__":
    window = GameWindow()
    window.setup()
    arcade.run()