from pyglet.window import key as pyglet_key


class InputState:
    def __init__(self):
        self.reset()
        self.window = None

    def reset(self):
        self.keys_pressed = set()
        self.keys_just_pressed = set()
        self.keys_just_released = set()

    def reset_frame_state(self):
        self.keys_just_pressed = set()
        self.keys_just_released = set()

    def set_window(self, window):
        self.window = window

    def update(self):
        if not self.window:
            return

        keys = {
            pyglet_key.UP, pyglet_key.DOWN, pyglet_key.LEFT, pyglet_key.RIGHT,
            pyglet_key.Z, pyglet_key.X,
            pyglet_key.RETURN, pyglet_key.ESCAPE,
            pyglet_key.A, pyglet_key.S,
            pyglet_key.MINUS, pyglet_key.EQUAL,
        }

        currently_pressed = self.window.pressed_keys.copy() & keys

        self.keys_just_pressed = currently_pressed - self.keys_pressed
        self.keys_just_released = self.keys_pressed - currently_pressed
        self.keys_pressed = currently_pressed

    def is_pressed(self, key):
        return key in self.keys_pressed

    def is_just_pressed(self, key):
        return key in self.keys_just_pressed

    def is_just_released(self, key):
        return key in self.keys_just_released

    def any_just_pressed(self):
        return len(self.keys_just_pressed) > 0