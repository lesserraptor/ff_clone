"""Party stat calculation (equipment bonuses)."""
from game.data import WEAPON_DATA, ARMOR_DATA


def calc_party_stats(party):
    for member in party:
        atk_bonus = 0
        def_bonus = 0
        mag_bonus = 0
        if member.weapon:
            w = WEAPON_DATA.get(member.weapon, {})
            atk_bonus += w.get("atk", 0)
            mag_bonus += w.get("mag", 0)
        if member.armor:
            a = ARMOR_DATA.get(member.armor, {})
            def_bonus += a.get("def", 0)
            mag_bonus += a.get("mag", 0)
        if member.helm:
            h = ARMOR_DATA.get(member.helm, {})
            def_bonus += h.get("def", 0)
        if member.shield:
            s = ARMOR_DATA.get(member.shield, {})
            def_bonus += s.get("def", 0)
        if member.accessory:
            a = ARMOR_DATA.get(member.accessory, {})
            def_bonus += a.get("def", 0)
            mag_bonus += a.get("mag", 0)
            atk_bonus += a.get("atk", 0)
        member.atk = member.base_atk + atk_bonus
        member.def_ = member.base_def + def_bonus
        member.mag = mag_bonus


def apply_level_ups_to_actors(actors) -> list[dict]:
    """Apply level-ups to all living actors. Returns list of level-up events."""
    events = []
    for member in actors:
        if hasattr(member, 'alive') and member.alive:
            while member.exp >= member.exp_next:
                member.exp -= member.exp_next
                member.lvl += 1
                member.exp_next = int(member.exp_next * 1.5)
                member.hp_max += 5
                member.hp = member.hp_max
                member.atk += 2
                member.def_ += 1
                events.append({"member": member.name, "new_lvl": member.lvl})
    return events
