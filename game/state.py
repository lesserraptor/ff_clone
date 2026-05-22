"""GameEngine — top-level game state + scene switching."""
from game.dataclasses import PartyMember
from game.input import InputState
from game.scene_registry import SCENES
from game.stats import calc_party_stats

DEFAULT_PARTY = [
    {"name": "Warrior", "job": "Warrior", "hp": 50, "hp_max": 50, "mp": 0, "mp_max": 0, "atk": 12, "def": 5, "lvl": 1, "exp": 0, "exp_next": 100,
     "weapon": "iron_sword", "armor": "leather_armor", "helm": None, "shield": None, "accessory": None,
     "spells": [], "status": []},
    {"name": "Wizard", "job": "Wizard", "hp": 35, "hp_max": 35, "mp": 30, "mp_max": 30, "atk": 6, "def": 2, "lvl": 1, "exp": 0, "exp_next": 100,
     "weapon": "iron_staff", "armor": "mage_robe", "helm": None, "shield": None, "accessory": None,
     "spells": ["fire", "ice", "thunder", "cure"], "status": []},
    {"name": "Rogue", "job": "Rogue", "hp": 40, "hp_max": 40, "mp": 0, "mp_max": 0, "atk": 10, "def": 4, "lvl": 1, "exp": 0, "exp_next": 100,
     "weapon": "dagger", "armor": "leather_armor", "helm": None, "shield": None, "accessory": None,
     "spells": [], "status": []},
    {"name": "Healer", "job": "Healer", "hp": 30, "hp_max": 30, "mp": 40, "mp_max": 40, "atk": 6, "def": 3, "lvl": 1, "exp": 0, "exp_next": 100,
     "weapon": "wooden_staff", "armor": "mage_robe", "helm": None, "shield": None, "accessory": None,
     "spells": ["cure", "raise", "esuna"], "status": []},
]


class GameEngine:
    def __init__(self, window):
        self.window = window
        self.input = InputState()
        self.input.set_window(window)
        self.scene = None
        self.scene_name = None
        self.party = None
        self._pending_scene = None
        self.play_time = 0
        self.inventory = []
        self.gold = 0
        self.current_map = "overworld_1"
        self.player_x = 7
        self.player_y = 5
        self.equip_item_pool = []
        self._scene_cooldown = 0
        self._event_queue: list = []

    def new_game(self):
        self.party = [PartyMember.from_dict(p) for p in DEFAULT_PARTY]
        calc_party_stats(self.party)
        self.inventory = [
            {"id": "potion", "qty": 5},
            {"id": "hi_potion", "qty": 2},
            {"id": "ether", "qty": 2},
            {"id": "phoenix_down", "qty": 1},
            {"id": "tent", "qty": 1},
            {"id": "iron_sword", "qty": 1},
            {"id": "leather_armor", "qty": 1},
            {"id": "steel_shield", "qty": 1},
            {"id": "iron_helm", "qty": 1},
            {"id": "power_ring", "qty": 1},
        ]
        self.gold = 150
        self.current_map = "overworld_1"
        self.player_x = 7
        self.player_y = 5
        self.play_time = 0

    def get_state(self):
        return {
            "party": [p.to_dict() for p in self.party],
            "inventory": self.inventory,
            "gold": self.gold,
            "current_map": self.current_map,
            "player_x": self.player_x,
            "player_y": self.player_y,
            "play_time": self.play_time,
            "equip_pool": self.equip_item_pool,
        }

    def load_state(self, state):
        self.party = [PartyMember.from_dict(p) for p in state.get("party", [])]
        self.inventory = state.get("inventory", [])
        self.gold = state.get("gold", 0)
        self.current_map = state.get("current_map", "overworld_1")
        self.player_x = state.get("player_x", 7)
        self.player_y = state.get("player_y", 5)
        self.play_time = state.get("play_time", 0)
        self.equip_item_pool = state.get("equip_pool", [])
        if self.party:
            calc_party_stats(self.party)

    def set_scene(self, name):
        if self.scene_name == name:
            return
        SceneClass = SCENES.get(name)
        if not SceneClass:
            raise ValueError(f"Unknown scene: {name}")
        self.scene_name = name
        self.scene = SceneClass(self)
        self.input.reset_frame_state()
        self._scene_cooldown = 2

    def push_event(self, event):
        """Add an event to the queue for deferred processing."""
        from game.events import GameEvent
        self._event_queue.append(event)

    def process_events(self):
        """Process queued events. Called at end of update()."""
        while self._event_queue:
            event = self._event_queue.pop(0)
            self._handle_event(event)

    def _handle_event(self, event):
        from game.events import GameEventType
        if event.type == GameEventType.SCENE_CHANGE:
            self.set_scene(event.data.get("name", ""))
        elif event.type == GameEventType.BATTLE_START:
            self.set_scene("battle")
        elif event.type == GameEventType.EXIT_MAP:
            if "dest_map" in event.data:
                self.current_map = event.data["dest_map"]
                self.player_x = event.data["dest_x"]
                self.player_y = event.data["dest_y"]
            self.set_scene("overworld")
        elif event.type == GameEventType.MENU_OPEN:
            self.set_scene("menu")

    def update(self, delta_time):
        self.play_time += delta_time
        if self._scene_cooldown > 0:
            self._scene_cooldown -= 1
        self.input.update()
        if self.scene:
            self.scene.update(delta_time)
        self.process_events()

    def draw(self):
        if self.scene:
            self.scene.draw()

    def get_scale(self):
        return self.window.scale_factor

    def get_size(self):
        return self.window.width, self.window.height

    def get_layout_context(self):
        from game.layout import LayoutContext
        return LayoutContext(
            scale=self.get_scale(),
            width=self.get_size()[0],
            height=self.get_size()[1],
            me=int(self.get_scale()),
        )

    def add_item(self, item_id, qty=1):
        for entry in self.inventory:
            if entry["id"] == item_id:
                entry["qty"] += qty
                return True
        self.inventory.append({"id": item_id, "qty": qty})
        return True

    def remove_item(self, item_id, qty=1):
        for entry in self.inventory:
            if entry["id"] == item_id:
                if entry["qty"] <= qty:
                    self.inventory.remove(entry)
                else:
                    entry["qty"] -= qty
                return True
        return False

    def has_item(self, item_id):
        for entry in self.inventory:
            if entry["id"] == item_id:
                return entry["qty"]
        return 0

    def get_item_count(self):
        return sum(e["qty"] for e in self.inventory)
