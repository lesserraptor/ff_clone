"""Tests for PartyMember dataclass."""
from game.dataclasses import PartyMember


class TestPartyMember:
    def test_create_default(self):
        pm = PartyMember(name="Hero")
        assert pm.name == "Hero"
        assert pm.hp == 50
        assert pm.hp_max == 50
        assert pm.alive is True

    def test_take_damage(self):
        pm = PartyMember(name="Hero", hp=50, hp_max=50)
        pm.take_damage(20)
        assert pm.hp == 30
        assert pm.alive is True

    def test_take_damage_lethal(self):
        pm = PartyMember(name="Hero", hp=50, hp_max=50)
        pm.take_damage(50)
        assert pm.hp == 0
        assert pm.alive is False

    def test_take_damage_overkill(self):
        pm = PartyMember(name="Hero", hp=50, hp_max=50)
        pm.take_damage(999)
        assert pm.hp == 0
        assert pm.alive is False

    def test_heal(self):
        pm = PartyMember(name="Hero", hp=30, hp_max=50)
        pm.heal(10)
        assert pm.hp == 40

    def test_heal_cant_exceed_max(self):
        pm = PartyMember(name="Hero", hp=30, hp_max=50)
        pm.heal(100)
        assert pm.hp == 50

    def test_is_alive(self):
        pm = PartyMember(name="Hero", hp=50, hp_max=50)
        assert pm.is_alive() is True
        pm.take_damage(50)
        assert pm.is_alive() is False

    def test_to_dict(self):
        pm = PartyMember(name="Warrior", hp=30, hp_max=50, base_atk=12, base_def=5)
        d = pm.to_dict()
        assert d["name"] == "Warrior"
        assert d["hp"] == 30
        assert d["base_atk"] == 12
        assert "atk" not in d  # computed field
        assert "def" not in d   # computed field
        assert d["spells"] == []

    def test_from_dict_roundtrip(self):
        pm = PartyMember(name="Test", hp=30, hp_max=50, mp=10, mp_max=30,
                         base_atk=12, base_def=5, spd=8, lvl=2,
                         weapon="iron_sword", armor="leather_armor",
                         spells=["fire", "cure"])
        d = pm.to_dict()
        pm2 = PartyMember.from_dict(d)
        assert pm2.name == pm.name
        assert pm2.hp == pm.hp
        assert pm2.hp_max == pm.hp_max
        assert pm2.mp == pm.mp
        assert pm2.mp_max == pm.mp_max
        assert pm2.base_atk == pm.base_atk
        assert pm2.base_def == pm.base_def
        assert pm2.spd == pm.spd
        assert pm2.lvl == pm.lvl
        assert pm2.weapon == pm.weapon
        assert pm2.armor == pm.armor
        assert pm2.spells == pm.spells

    def test_from_dict_legacy_fields(self):
        """Should handle old save format with atk/def/level/xp."""
        pm = PartyMember.from_dict({
            "name": "Legacy",
            "hp": 40, "hp_max": 50,
            "atk": 12, "def": 5,
            "level": 3, "xp": 50, "xp_next": 200,
        })
        assert pm.base_atk == 12
        assert pm.base_def == 5
        assert pm.lvl == 3
        assert pm.exp == 50
        assert pm.exp_next == 200

    def test_default_spells_is_new_list(self):
        pm1 = PartyMember(name="A")
        pm2 = PartyMember(name="B")
        pm1.spells.append("fire")
        assert len(pm2.spells) == 0  # not shared
