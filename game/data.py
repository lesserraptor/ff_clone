"""Game data loading — JSON → global dicts."""
ITEM_DATA: dict = {}
SPELL_DATA: dict = {}
WEAPON_DATA: dict = {}
ARMOR_DATA: dict = {}


def load_game_data():
    global ITEM_DATA, SPELL_DATA, WEAPON_DATA, ARMOR_DATA
    import json
    base = "data"
    with open(f"{base}/items.json") as f:
        items = json.load(f)
    ITEM_DATA = items.get("items", {})
    WEAPON_DATA = items.get("weapons", {})
    ARMOR_DATA = items.get("armor", {})
    with open(f"{base}/spells.json") as f:
        spells = json.load(f)
    SPELL_DATA = spells.get("spells", {})


def get_item(id):
    if id in ITEM_DATA:
        return {**ITEM_DATA[id], "id": id, "category": "item"}
    if id in WEAPON_DATA:
        return {**WEAPON_DATA[id], "id": id, "category": "weapon"}
    if id in ARMOR_DATA:
        return {**ARMOR_DATA[id], "id": id, "category": "armor"}
    return None
