"""Game package - entry point for game initialization."""

def init_game():
    """Initialize game data and database. Call once at startup before creating window."""
    from game.data import load_game_data
    from game.save import init_db
    load_game_data()
    init_db()
