from __future__ import annotations

import arcade

from hive_game.hive.game_window import GameWindow

def main() -> None:
    """Main function to set up and run the game."""
    window = GameWindow()
    arcade.run()

if __name__ == "__main__":
    main() 