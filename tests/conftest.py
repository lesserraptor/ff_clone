"""Test configuration - adds project root to path and initializes game data."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game import init_game
init_game()
