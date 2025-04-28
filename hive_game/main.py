from __future__ import annotations

import arcade
import sys
import os

# Ensure the package root is in sys.path when running as script
sys.path.insert(0, os.path.dirname(__file__))

from hive.game_window import GameWindow
from hive_game.hive import config

def main() -> None:
    """Main function to set up and run the game."""
    window = GameWindow()
    arcade.run()

if __name__ == "__main__":
    main() 