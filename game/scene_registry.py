"""Scene class registry — decorator + lookup."""
SCENES: dict = {}


def register_scene(name):
    def decorator(cls):
        SCENES[name] = cls
        return cls
    return decorator
