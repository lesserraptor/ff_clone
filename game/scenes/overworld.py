from game.scene_registry import register_scene
from game.scenes.overworld_states import OverworldModel, OverworldRenderer


@register_scene("overworld")
class OverworldScene:
    """Thin coordinator that delegates to model + renderer."""

    def __init__(self, engine):
        self.engine = engine
        from game.scenes.overworld_states import load_maps, load_enemies
        tile_defs, maps, scripts = load_maps()
        enemy_data = load_enemies()
        self.model = OverworldModel(engine, tile_defs, maps, scripts, enemy_data)
        self.renderer = OverworldRenderer()

    def update(self, dt):
        event = self.model.update(dt, self.engine.input)

        # Sync engine state from model so scene switches preserve position
        self.engine.player_x = self.model.player_tile_x
        self.engine.player_y = self.model.player_tile_y

        if event:
            self._handle_event(event)

    def _handle_event(self, event):
        if event["type"] == "battle":
            self.engine.set_scene("battle")
        elif event["type"] == "menu":
            self.engine.set_scene("menu")
        elif event["type"] == "exit":
            self.engine.current_map = event["dest_map"]
            self.engine.player_x = event["dest_x"]
            self.engine.player_y = event["dest_y"]

            self.model.player_tile_x = event["dest_x"]
            self.model.player_tile_y = event["dest_y"]
            self.model.target_tile_x = event["dest_x"]
            self.model.target_tile_y = event["dest_y"]
            self.model.load_map(event["dest_map"])

    def draw(self):
        ctx = self.engine.get_layout_context()
        self.renderer.draw(self.model, ctx.scale, ctx.width, ctx.height)
