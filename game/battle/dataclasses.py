from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class ActionType(Enum):
    PARTY_ATTACK = auto()
    PARTY_MAGIC = auto()
    ENEMY_ATTACK = auto()
    USE_ITEM = auto()
    RUN = auto()


class SpellType(Enum):
    ATTACK = auto()
    HEAL = auto()
    REVIVE = auto()
    CURE_STATUS = auto()
    BUFF = auto()
    DEBUFF = auto()


class SpellTarget(Enum):
    ENEMY = auto()
    ALLY = auto()
    SELF = auto()


@dataclass
class Spell:
    id: str
    name: str
    spell_type: SpellType
    target: SpellTarget
    power: int = 10
    mp_cost: int = 0
    description: str = ""


@dataclass
class Actor:
    name: str
    hp: int
    hp_max: int
    atk: int
    def_: int
    spd: int
    alive: bool = True
    mp: int = 0
    mp_max: int = 0
    lvl: int = 1
    exp: int = 0
    exp_next: int = 100
    xp: int = 0
    gold: int = 0
    spells: list[str] = field(default_factory=list)
    is_enemy: bool = False
    dying_timer: float = 0.0

    @property
    def level(self) -> int:
        return self.lvl

    @property
    def xp_next(self) -> int:
        return self.exp_next


@dataclass
class Action:
    actor: Actor
    action_type: ActionType
    target: Optional[Actor] = None
    spell: Optional[Spell] = None
    spell_id: str = ""
    spell_name: str = ""


@dataclass
class BattleEvent:
    message: str
    actor: Actor
    target: Optional[Actor] = None
    damage: int = 0
    healed: int = 0
    is_death: bool = False
    is_victory: bool = False
    is_defeat: bool = False
    is_level_up: bool = False
    level_ups: int = 0
    xp_gained: int = 0
    gold_gained: int = 0
    death_message: str = ""
    apply_death: Optional[Actor] = None


def actor_from_dict(data: dict, is_enemy: bool = False) -> Actor:
    return Actor(
        name=data.get("name", ""),
        hp=data.get("hp", data.get("hp_max", 50)),
        hp_max=data.get("hp_max", 50),
        mp=data.get("mp", 0),
        mp_max=data.get("mp_max", 0),
        atk=data.get("atk", 10),
        def_=data.get("def", 5),
        spd=data.get("spd", 10),
        alive=data.get("hp", data.get("hp_max", 50)) > 0,
        lvl=data.get("lvl", data.get("level", 1)),
        exp=data.get("exp", data.get("xp", 0)),
        exp_next=data.get("exp_next", data.get("xp_next", 100)),
        spells=data.get("spells", []),
        is_enemy=is_enemy,
    )


def actor_to_dict(actor: Actor) -> dict:
    return {
        "name": actor.name,
        "hp": actor.hp,
        "hp_max": actor.hp_max,
        "mp": actor.mp,
        "mp_max": actor.mp_max,
        "atk": actor.atk,
        "def": actor.def_,
        "spd": actor.spd,
        "alive": actor.alive,
        "lvl": actor.lvl,
        "exp": actor.exp,
        "exp_next": actor.exp_next,
        "spells": actor.spells,
    }