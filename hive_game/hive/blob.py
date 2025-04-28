from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field

import arcade

from hive_game.hive import config
from hive_game.hive.world import World, ResourceType

@dataclass
class Blob:
    """Represents a single blob creature in the simulation."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    x: int = 0
    y: int = 0
    color: tuple[int, int, int] = field(default_factory=lambda: random.choice([
        arcade.color.RED,
        arcade.color.BLUE,
        arcade.color.GREEN,
        arcade.color.YELLOW,
        arcade.color.PURPLE,
        arcade.color.ORANGE
    ]))
    hunger: int = 0 # 0 = full, config.BLOB_MAX_NEEDS = starving
    thirst: int = 0 # 0 = full, config.BLOB_MAX_NEEDS = dying
    energy: int = 100 # Example, not fully used in Phase 1
    alive: bool = True

    _hunger_rate_tick: float = config.HUNGER_RATE / config.TICK_RATE_HZ
    _thirst_rate_tick: float = config.THIRST_RATE / config.TICK_RATE_HZ
    _energy_decay_tick: float = config.ENERGY_DECAY / config.TICK_RATE_HZ

    def update(self, world: World, dt: float) -> None:
        """Updates the blob's state for one tick.

        Args:
            world: The world object containing resource information.
            dt: Delta time since the last update.
        """
        if not self.alive:
            return

        # Update needs
        self.hunger += self._hunger_rate_tick * config.TICK_RATE_HZ # Simplified for now
        self.thirst += self._thirst_rate_tick * config.TICK_RATE_HZ
        self.energy -= self._energy_decay_tick * config.TICK_RATE_HZ
        self.hunger = min(max(0, int(self.hunger)), config.BLOB_MAX_NEEDS)
        self.thirst = min(max(0, int(self.thirst)), config.BLOB_MAX_NEEDS)
        self.energy = max(0, int(self.energy))

        # Check for death
        if self.hunger >= config.BLOB_MAX_NEEDS or self.thirst >= config.BLOB_MAX_NEEDS:
            self.alive = False
            return # Stop processing if dead

        # Check for resources at current location
        current_tile = world.get_tile(self.x, self.y)
        if current_tile == ResourceType.FOOD:
            self.hunger = max(0, self.hunger - config.FOOD_FILL)
            world.consume_tile(self.x, self.y)
        elif current_tile == ResourceType.WATER:
            self.thirst = max(0, self.thirst - config.WATER_FILL)
            world.consume_tile(self.x, self.y)

        # Random wander movement
        self._wander(world)

    def _wander(self, world: World) -> None:
        """Moves the blob randomly one step in a cardinal or diagonal direction."""
        dx = random.choice([-config.GRID_STEP, 0, config.GRID_STEP])
        dy = random.choice([-config.GRID_STEP, 0, config.GRID_STEP])

        # Prevent moving outside world boundaries
        new_x = max(0, min(world.width - config.BLOB_SIZE, self.x + dx))
        new_y = max(0, min(world.height - config.BLOB_SIZE, self.y + dy))

        self.x = new_x
        self.y = new_y

    def draw(self) -> None:
        """Draws the blob as a simple rectangle."""
        if self.alive:
            arcade.draw_rectangle_filled(
                center_x=self.x + config.BLOB_SIZE / 2,
                center_y=self.y + config.BLOB_SIZE / 2,
                width=config.BLOB_SIZE,
                height=config.BLOB_SIZE,
                color=self.color
            ) 