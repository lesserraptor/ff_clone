import random
from typing import Optional
from game.battle.dataclasses import (
    Actor, Action, ActionType, BattleEvent, Spell, SpellType, SpellTarget
)
from game.battle.engine import SpeedQueue, calc_damage


class BattleModel:
    def __init__(self, party_data: list[dict], enemy_data: dict, spells: dict, map_id: str = "", item_data: dict = None):
        self.spells = spells
        self.item_data = item_data or {}
        self.rewards = {"xp": 0, "gold": 0, "items": []}
        self.party: list[Actor] = []
        self.enemies: list[Actor] = []
        self.action_queue = SpeedQueue()
        self.party_actions: dict[int, dict] = {}
        self.current_action: Optional[Action] = None
        self.used_items: list[str] = []

        self._init_party(party_data)
        self._init_enemies(enemy_data, map_id)

    def _init_party(self, party_data: list[dict]) -> None:
        for p in party_data:
            self.party.append(Actor(
                name=p.get("name", ""),
                hp=p.get("hp", p.get("hp_max", 50)),
                hp_max=p.get("hp_max", 50),
                mp=p.get("mp", 0),
                mp_max=p.get("mp_max", 0),
                atk=p.get("atk", 10),
                def_=p.get("def", 5),
                spd=p.get("spd", 10),
                alive=p.get("hp", p.get("hp_max", 50)) > 0,
                lvl=p.get("lvl", 1),
                exp=p.get("exp", 0),
                exp_next=p.get("exp_next", 100),
                spells=p.get("spells", []),
                is_enemy=False,
            ))

    def _init_enemies(self, enemy_data: dict, map_id: str) -> None:
        encounter_list = enemy_data.get("encounters", {}).get(map_id, [])
        if not encounter_list:
            encounter_list = list(enemy_data.get("enemies", {}).keys())

        enemy_ids = random.sample(
            encounter_list, 
            min(random.randint(1, 2), len(encounter_list))
        )

        for eid in enemy_ids:
            e = enemy_data["enemies"][eid]
            self.enemies.append(Actor(
                name=e.get("name", eid),
                hp=e.get("hp", 20),
                hp_max=e.get("hp_max", 20),
                atk=e.get("atk", 5),
                def_=e.get("def", 2),
                spd=e.get("spd", 5),
                alive=True,
                xp=e.get("xp", 10),
                gold=e.get("gold", 5),
                is_enemy=True,
            ))

    def get_living_party(self) -> list[Actor]:
        return [p for p in self.party if p.alive]

    def get_living_enemies(self) -> list[Actor]:
        return [e for e in self.enemies if e.alive]

    def prepare_enemy_turn(self):
        """Only enemies act (when escape attempt fails)."""
        self.action_queue.clear()
        for enemy in self.get_living_enemies():
            living_party = self.get_living_party()
            if living_party:
                target = random.choice(living_party)
                act = Action(
                    actor=enemy,
                    action_type=ActionType.ENEMY_ATTACK,
                    target=target,
                )
                self.action_queue.add(act)

    def get_next_party_member(self, current_idx: int) -> Optional[Actor]:
        living = self.get_living_party()
        for i in range(len(living)):
            idx = (current_idx + 1 + i) % len(living)
            if idx not in self.party_actions:
                return living[idx]
        return None

    def has_all_party_acted(self) -> bool:
        living = self.get_living_party()
        return all(
            self.party.index(p) in self.party_actions 
            for p in living
        )

    def queue_party_action(self, member_idx: int, action_type: str, target_idx: int, spell_id: str = "") -> None:
        self.party_actions[member_idx] = {
            "type": action_type,
            "target": target_idx,
            "spell_id": spell_id,
        }

    def has_party_action(self, member_idx: int) -> bool:
        return member_idx in self.party_actions

    def prepare_battle(self) -> None:
        self.action_queue.clear()

        for idx, action in self.party_actions.items():
            member = self.party[idx]
            if not member.alive:
                continue

            target_idx = action["target"]
            if action["type"] == "magic":
                spell_id = action["spell_id"]
                spell = self._get_spell(spell_id)
                target = self._get_target(spell, target_idx)
                if target:
                    act = Action(
                        actor=member,
                        action_type=ActionType.PARTY_MAGIC,
                        target=target,
                        spell=spell,
                        spell_id=spell_id,
                        spell_name=spell.name if spell else spell_id,
                    )
                    self.action_queue.add(act)
            elif action["type"] == "item":
                item_id = action["spell_id"]
                item_def = self.item_data.get(item_id, {})
                target = None
                if target_idx < len(self.party):
                    target = self.party[target_idx]
                if target:
                    act = Action(
                        actor=member,
                        action_type=ActionType.USE_ITEM,
                        target=target,
                        spell_id=item_id,
                        spell_name=item_def.get("name", item_id),
                    )
                    self.action_queue.add(act)
            else:
                target = self.enemies[target_idx] if target_idx < len(self.enemies) else None
                if target:
                    act = Action(
                        actor=member,
                        action_type=ActionType.PARTY_ATTACK,
                        target=target,
                    )
                    self.action_queue.add(act)

        self.used_items.clear()

        for enemy in self.get_living_enemies():
            living_party = self.get_living_party()
            if living_party:
                target = random.choice(living_party)
                act = Action(
                    actor=enemy,
                    action_type=ActionType.ENEMY_ATTACK,
                    target=target,
                )
                self.action_queue.add(act)

        self.party_actions = {}

    def _get_spell(self, spell_id: str) -> Optional[Spell]:
        data = self.spells.get(spell_id, {})
        if not data:
            return None
        return Spell(
            id=spell_id,
            name=data.get("name", spell_id),
            spell_type=SpellType[data.get("type", "attack").upper()],
            target=SpellTarget.ENEMY if data.get("target", "enemy") == "enemy" else SpellTarget.ALLY,
            power=data.get("power", 10),
            mp_cost=data.get("mp_cost", 0),
            description=data.get("description", ""),
        )

    def _get_target(self, spell: Optional[Spell], target_idx: int) -> Optional[Actor]:
        if not spell:
            return None
        if spell.target == SpellTarget.ENEMY:
            if target_idx < len(self.enemies):
                return self.enemies[target_idx]
        else:
            if target_idx < len(self.party):
                return self.party[target_idx]
        return None

    def process_next_action(self) -> Optional[Action]:
        action = self.action_queue.pop()
        if not action:
            return None

        if not action.actor.alive:
            return self.process_next_action()

        if action.target:
            if action.target == action.actor:
                pass
            elif not action.target.alive:
                if action.action_type in (ActionType.PARTY_ATTACK, ActionType.PARTY_MAGIC):
                    living = self.get_living_enemies()
                    if living:
                        action.target = living[0]
                    else:
                        return self.process_next_action()
                else:
                    living = self.get_living_party()
                    if living:
                        action.target = living[0]
                    else:
                        return self.process_next_action()

        self.current_action = action
        return action

    def execute_action(self, action: Action) -> list[BattleEvent]:
        events = []

        if action.action_type == ActionType.PARTY_ATTACK:
            if not action.target or not action.target.alive:
                return events
            # Event 1: attack declaration
            events.append(BattleEvent(
                message=f"{action.actor.name} attacks {action.target.name}!",
                actor=action.actor,
                target=action.target,
            ))
            # Event 2: damage result
            dmg = calc_damage(action.actor.atk, action.target.def_)
            action.target.hp -= dmg
            events.append(BattleEvent(
                message=f"{action.actor.name} deals {dmg} damage to {action.target.name}!",
                actor=action.actor,
                target=action.target,
                damage=dmg,
            ))
            if action.target.hp <= 0:
                action.target.hp = 0
                events[-1].is_death = True
                events[-1].death_message = f"{action.target.name} is slain!"
                self.rewards["xp"] += action.target.xp
                self.rewards["gold"] += action.target.gold

                if not self.get_living_enemies():
                    return events

        elif action.action_type == ActionType.PARTY_MAGIC:
            if not action.target:
                return events
            spell = action.spell
            if not spell:
                return events

            action.actor.mp -= spell.mp_cost
            target_name = action.target.name

            if spell.spell_type == SpellType.ATTACK:
                if not action.target.alive:
                    return events
                # Event 1: cast declaration
                events.append(BattleEvent(
                    message=f"{action.actor.name} casts {spell.name} on {target_name}!",
                    actor=action.actor,
                    target=action.target,
                ))
                # Event 2: damage result
                dmg = max(1, spell.power - action.target.def_)
                action.target.hp -= dmg
                events.append(BattleEvent(
                    message=f"{spell.name} deals {dmg} damage to {target_name}!",
                    actor=action.actor,
                    target=action.target,
                    damage=dmg,
                ))
                if action.target.hp <= 0:
                    action.target.hp = 0
                    events[-1].is_death = True
                    events[-1].death_message = f"{target_name} is slain!"
                    self.rewards["xp"] += action.target.xp
                    self.rewards["gold"] += action.target.gold

            elif spell.spell_type == SpellType.HEAL:
                old_hp = action.target.hp
                action.target.hp = min(action.target.hp_max, action.target.hp + spell.power)
                healed = action.target.hp - old_hp
                events.append(BattleEvent(
                    message=f"{action.actor.name} casts {spell.name} on {target_name}! HP restored!",
                    actor=action.actor,
                    target=action.target,
                    healed=healed,
                ))

            elif spell.spell_type == SpellType.REVIVE:
                was_alive = action.target.alive
                action.target.alive = True
                action.target.hp = min(action.target.hp_max, spell.power)
                events.append(BattleEvent(
                    message=f"{action.actor.name} casts {spell.name} on {target_name}! {target_name} revived!",
                    actor=action.actor,
                    target=action.target,
                    healed=action.target.hp if was_alive else spell.power,
                ))

            else:
                events.append(BattleEvent(
                    message=f"{action.actor.name} casts {spell.name} on {target_name}!",
                    actor=action.actor,
                    target=action.target,
                ))

        elif action.action_type == ActionType.USE_ITEM:
            if not action.target:
                return events
            item_id = action.spell_id
            item_def = self.item_data.get(item_id, {})
            effect = item_def.get("effect", "")
            value = item_def.get("value", 0)
            target = action.target
            item_name = item_def.get("name", item_id)

            if effect == "heal":
                old_hp = target.hp
                target.hp = min(target.hp_max, target.hp + value)
                healed = target.hp - old_hp
                events.append(BattleEvent(
                    message=f"{action.actor.name} uses {item_name} on {target.name}! HP restored!",
                    actor=action.actor, target=target, healed=healed,
                ))
            elif effect == "revive":
                was_alive = target.alive
                target.alive = True
                target.hp = min(target.hp_max, value)
                events.append(BattleEvent(
                    message=f"{action.actor.name} uses {item_name} on {target.name}! {target.name} revived!",
                    actor=action.actor, target=target, healed=target.hp,
                ))
            elif effect == "mana":
                old_mp = target.mp
                target.mp = min(target.mp_max, target.mp + value)
                restored = target.mp - old_mp
                events.append(BattleEvent(
                    message=f"{action.actor.name} uses {item_name} on {target.name}! MP restored!",
                    actor=action.actor, target=target, healed=restored,
                ))
            elif effect in ("full_restore", "restore_all"):
                old_hp = target.hp
                target.hp = target.hp_max
                target.mp = target.mp_max
                events.append(BattleEvent(
                    message=f"{action.actor.name} uses {item_name} on {target.name}! Fully restored!",
                    actor=action.actor, target=target, healed=target.hp_max - old_hp,
                ))
            else:
                events.append(BattleEvent(
                    message=f"{action.actor.name} uses {item_name} on {target.name}!",
                    actor=action.actor, target=target,
                ))

            self.used_items.append(item_id)

        elif action.action_type == ActionType.ENEMY_ATTACK:
            if not action.target or not action.target.alive:
                return events
            # Event 1: attack declaration
            events.append(BattleEvent(
                message=f"{action.actor.name} attacks {action.target.name}!",
                actor=action.actor,
                target=action.target,
            ))
            # Event 2: damage result
            dmg = calc_damage(action.actor.atk, action.target.def_)
            action.target.hp -= dmg
            events.append(BattleEvent(
                message=f"{action.actor.name} deals {dmg} damage to {action.target.name}!",
                actor=action.actor,
                target=action.target,
                damage=dmg,
            ))
            if action.target.hp <= 0:
                action.target.hp = 0
                events[-1].is_death = True
                events[-1].death_message = f"{action.target.name} falls!"

        return events

    def check_battle_end(self) -> tuple[bool, bool]:
        victory = not any(e.alive for e in self.enemies)
        defeat = not any(p.alive for p in self.party)
        return victory, defeat

    def apply_level_ups(self) -> list[BattleEvent]:
        events = []
        for member in self.get_living_party():
            while member.exp >= member.exp_next:
                member.exp -= member.exp_next
                member.lvl += 1
                member.exp_next = int(member.exp_next * 1.5)
                member.hp_max += 5
                member.hp = member.hp_max
                member.atk += 2
                member.def_ += 1
                events.append(BattleEvent(
                    message=f"{member.name} levels up!",
                    actor=member,
                    is_level_up=True,
                    level_ups=1,
                ))
        return events

    def to_party_data(self) -> list[dict]:
        return [actor_to_dict(p) for p in self.party]
