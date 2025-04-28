from __future__ import annotations

import arcade
import sys
import os
import logging

# Ensure the package root is in sys.path when running as script
sys.path.insert(0, os.path.dirname(__file__))

from hive_game.hive.game_window import GameWindow
from hive_game.hive import config

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
LOG_LEVEL = logging.INFO
LOG_FILENAME = "hive_game.log"

def setup_logging() -> None:
    """Configures logging to file and console."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILENAME, mode='w'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("Logging configured.")

def main() -> None:
    """Main function to set up and run the game."""
    setup_logging()
    logging.info(f"Starting HiveLife Simulation (Tick Rate: {config.TICK_RATE_HZ} Hz)")
    window = GameWindow()
    try:
        arcade.run()
    finally:
        logging.info("HiveLife Simulation ended.")

if __name__ == "__main__":
    main() 