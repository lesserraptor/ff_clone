from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PartyMember:
    name: str
    job: str = ""
    hp: int = 50
    hp_max: int = 50
    mp: int = 0
    mp_max: int = 0
    base_atk: int = 10
    base_def: int = 5
    spd: int = 10
    lvl: int = 1
    exp: int = 0
    exp_next: int = 100
    alive: bool = True
    weapon: Optional[str] = None
    armor: Optional[str] = None
    helm: Optional[str] = None
    shield: Optional[str] = None
    spells: list[str] = field(default_factory=list)
    status: list[str] = field(default_factory=list)
    mag: int = 0
    # The following are overwritten by calc_party_stats() using base + equipment:
    atk: int = 10
    def_: int = 5

    def is_alive(self) -> bool:
        return self.alive

    def take_damage(self, amount: int):
        self.hp = max(0, self.hp - amount)
        if self.hp <= 0:
            self.alive = False

    def heal(self, amount: int):
        self.hp = min(self.hp_max, self.hp + amount)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "job": self.job,
            "hp": self.hp,
            "hp_max": self.hp_max,
            "mp": self.mp,
            "mp_max": self.mp_max,
            "base_atk": self.base_atk,
            "base_def": self.base_def,
            "spd": self.spd,
            "lvl": self.lvl,
            "exp": self.exp,
            "exp_next": self.exp_next,
            "alive": self.alive,
            "weapon": self.weapon,
            "armor": self.armor,
            "helm": self.helm,
            "shield": self.shield,
            "spells": list(self.spells),
            "status": list(self.status),
        }

    @staticmethod
    def from_dict(d: dict) -> "PartyMember":
        return PartyMember(
            name=d["name"],
            job=d.get("job", ""),
            hp=d.get("hp", d.get("hp_max", 50)),
            hp_max=d.get("hp_max", 50),
            mp=d.get("mp", 0),
            mp_max=d.get("mp_max", 0),
            base_atk=d.get("base_atk", d.get("atk", 10)),
            base_def=d.get("base_def", d.get("def", 5)),
            spd=d.get("spd", 10),
            lvl=d.get("lvl", d.get("level", 1)),
            exp=d.get("exp", d.get("xp", 0)),
            exp_next=d.get("exp_next", d.get("xp_next", 100)),
            alive=d.get("alive", d.get("hp", 50) > 0),
            weapon=d.get("weapon"),
            armor=d.get("armor"),
            helm=d.get("helm"),
            shield=d.get("shield"),
            spells=d.get("spells", []),
            status=d.get("status", []),
        )
