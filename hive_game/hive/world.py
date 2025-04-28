from __future__ import annotations

import random
import enum
from typing import Dict, Tuple, TYPE_CHECKING

from hive_game.hive import config

if TYPE_CHECKING:
    from hive_game.hive.blob import Blob # Avoid circular import

class ResourceType(enum.IntEnum):
    """Enum for tile types."""
    EMPTY = 0
    FOOD = 1
    WATER = 2

# Type alias for coordinates
Coord = Tuple[int, int]

class World:
    """Represents the simulation world grid and resources."""

    def __init__(self, width: int, height: int):
        """Initializes the world.

        Args:
            width: The width of the world grid in pixels.
            height: The height of the world grid in pixels.
        """
        self.width = width
        self.height = height
        self.grid_width = width // config.GRID_STEP
        self.grid_height = height // config.GRID_STEP
        self.tiles: Dict[Coord, ResourceType] = {}

    def _get_random_empty_coord(self) -> Coord | None:
        """Finds a random empty grid coordinate."""
        attempts = 0
        max_attempts = self.grid_width * self.grid_height * 2 # Avoid infinite loop
        while attempts < max_attempts:
            gx = random.randrange(self.grid_width)
            gy = random.randrange(self.grid_height)
            coord = (gx * config.GRID_STEP, gy * config.GRID_STEP)
            if self.get_tile(coord[0], coord[1]) == ResourceType.EMPTY:
                return coord
            attempts += 1
        return None # No empty space found

    def spawn_resources(self, food_n: int, water_n: int) -> None:
        """Spawns food and water at random empty locations.

        Args:
            food_n: Number of food tiles to spawn.
            water_n: Number of water tiles to spawn.
        """
        for _ in range(food_n):
            coord = self._get_random_empty_coord()
            if coord:
                self.tiles[coord] = ResourceType.FOOD

        for _ in range(water_n):
            coord = self._get_random_empty_coord()
            if coord:
                self.tiles[coord] = ResourceType.WATER

    def get_tile(self, x: int, y: int) -> ResourceType:
        """Gets the resource type at a specific pixel coordinate.

        Args:
            x: The x-coordinate (pixels).
            y: The y-coordinate (pixels).

        Returns:
            The ResourceType at the given coordinate.
        """
        # Align to grid
        gx = (x // config.GRID_STEP) * config.GRID_STEP
        gy = (y // config.GRID_STEP) * config.GRID_STEP
        return self.tiles.get((gx, gy), ResourceType.EMPTY)

    def consume_tile(self, x: int, y: int) -> None:
        """Removes the resource at a specific pixel coordinate.

        Args:
            x: The x-coordinate (pixels).
            y: The y-coordinate (pixels).
        """
        gx = (x // config.GRID_STEP) * config.GRID_STEP
        gy = (y // config.GRID_STEP) * config.GRID_STEP
        coord = (gx, gy)
        if coord in self.tiles:
            del self.tiles[coord]

    def tile_is_food(self, x: int, y: int) -> bool:
        """Checks if the tile at the coordinates contains food."""
        return self.get_tile(x, y) == ResourceType.FOOD

    def tile_is_water(self, x: int, y: int) -> bool:
        """Checks if the tile at the coordinates contains water."""
        return self.get_tile(x, y) == ResourceType.WATER

    def tile_is_empty(self, x: int, y: int) -> bool:
        """Checks if the tile at the coordinates is empty."""
        # Considers out-of-bounds implicitly empty via get_tile logic
        return self.get_tile(x, y) == ResourceType.EMPTY 