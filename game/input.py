from pyglet.window import key as pyglet_key

UP = pyglet_key.UP
DOWN = pyglet_key.DOWN
LEFT = pyglet_key.LEFT
RIGHT = pyglet_key.RIGHT
ENTER = pyglet_key.RETURN
ESCAPE = pyglet_key.ESCAPE
Z = pyglet_key.Z
X = pyglet_key.X
A = pyglet_key.A
S = pyglet_key.S
MINUS = pyglet_key.MINUS
EQUAL = pyglet_key.EQUAL


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
            UP, DOWN, LEFT, RIGHT,
            Z, X,
            ENTER, ESCAPE,
            A, S,
            MINUS, EQUAL,
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