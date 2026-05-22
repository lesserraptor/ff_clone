"""Event system for scene transitions and game events."""
from dataclasses import dataclass, field
from enum import Enum, auto


class GameEventType(Enum):
    SCENE_CHANGE = auto()
    BATTLE_START = auto()
    EXIT_MAP = auto()
    MENU_OPEN = auto()


@dataclass
class GameEvent:
    type: GameEventType
    data: dict = field(default_factory=dict)
