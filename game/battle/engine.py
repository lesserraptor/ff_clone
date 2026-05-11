from typing import Optional
from game.battle.dataclasses import Action, Actor, ActionType


def calc_damage(atk: int, def_: int) -> int:
    return max(1, atk - def_)


class SpeedQueue:
    def __init__(self):
        self.queue: list[Action] = []

    def add(self, action: Action) -> None:
        self.queue.append(action)
        self.queue.sort(key=lambda a: a.actor.spd, reverse=True)

    def pop(self) -> Optional[Action]:
        if self.queue:
            return self.queue.pop(0)
        return None

    def clear(self) -> None:
        self.queue = []

    def __len__(self) -> int:
        return len(self.queue)

    def is_empty(self) -> bool:
        return len(self.queue) == 0


def create_action(
    actor: Actor,
    action_type: ActionType,
    target: Optional[Actor] = None,
    spell_id: str = "",
    spell_name: str = "",
) -> Action:
    return Action(
        actor=actor,
        action_type=action_type,
        target=target,
        spell_id=spell_id,
        spell_name=spell_name,
    )