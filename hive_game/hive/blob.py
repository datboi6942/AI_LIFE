from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import Optional, Tuple

import arcade

from hive_game.hive import config
from hive_game.hive.world import World, ResourceType

def _clamp(value: int, low: int, high: int) -> int:
    """Clamps an integer value between low and high."""
    return max(low, min(value, high))

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

    # --- Phase 2 Memory ---
    last_food_pos: Optional[Tuple[int, int]] = None
    last_water_pos: Optional[Tuple[int, int]] = None
    food_mem_age: float = 0.0   # seconds
    water_mem_age: float = 0.0

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

        # --- Memory Decay ---
        self._decay_mem(dt, world)

        # --- Update Needs ---
        # Note: Needs update *after* decay, so memory reflects state *before* current tick need increase
        self.hunger += self._hunger_rate_tick # Rate is per second, dt handles the fraction
        self.thirst += self._thirst_rate_tick
        self.energy -= self._energy_decay_tick
        self.hunger = min(max(0, int(self.hunger)), config.BLOB_MAX_NEEDS)
        self.thirst = min(max(0, int(self.thirst)), config.BLOB_MAX_NEEDS)
        self.energy = max(0, int(self.energy))

        # --- Check for Death ---
        if self.hunger >= config.BLOB_MAX_NEEDS or self.thirst >= config.BLOB_MAX_NEEDS:
            self.alive = False
            return # Stop processing if dead

        # --- Check for Resources at Current Location & Update Memory ---
        current_tile_type = world.get_tile(self.x, self.y)
        if current_tile_type == ResourceType.FOOD:
            self.hunger = max(0, self.hunger - config.FOOD_FILL)
            self.last_food_pos = (self.x, self.y) # Store current pos
            self.food_mem_age = 0.0 # Reset age
            world.consume_tile(self.x, self.y)
        elif current_tile_type == ResourceType.WATER:
            self.thirst = max(0, self.thirst - config.WATER_FILL)
            self.last_water_pos = (self.x, self.y) # Store current pos
            self.water_mem_age = 0.0 # Reset age
            world.consume_tile(self.x, self.y)

        # --- Movement (Seeking or Wandering) ---
        self._move(world)

    def _decay_mem(self, dt: float, world: World) -> None:
        """Decays memory age and invalidates memories if too old or tile is empty."""
        if self.last_food_pos:
            self.food_mem_age += dt
            # Check age OR if the tile is no longer food (e.g., another blob ate it)
            if self.food_mem_age > config.MEMORY_SPAN_S or not world.tile_is_food(*self.last_food_pos):
                self.last_food_pos = None
                self.food_mem_age = 0.0

        if self.last_water_pos:
            self.water_mem_age += dt
            if self.water_mem_age > config.MEMORY_SPAN_S or not world.tile_is_water(*self.last_water_pos):
                self.last_water_pos = None
                self.water_mem_age = 0.0

    def _decide_target(self) -> tuple[int, int] | None:
        """Decides the target coordinates based on needs and memory."""
        need_food = self.hunger >= config.HUNGER_SEEK and self.last_food_pos is not None
        need_water = self.thirst >= config.THIRST_SEEK and self.last_water_pos is not None

        if need_food and need_water:
            # Prioritize the greater need, hunger breaks ties
            if self.hunger >= self.thirst:
                return self.last_food_pos
            else:
                return self.last_water_pos
        elif need_food:
            return self.last_food_pos
        elif need_water:
            return self.last_water_pos
        else:
            return None # No urgent need or no memory

    def _move(self, world: World) -> None:
        """Moves the blob towards a target if seeking, otherwise wanders randomly."""
        target = self._decide_target()
        dx = 0
        dy = 0

        if target:
            # Seek target
            target_x, target_y = target
            # Calculate direction vector components
            delta_x = target_x - self.x
            delta_y = target_y - self.y

            # Simple axis-aligned movement towards target
            if delta_x > 0:
                dx = config.SEEK_SPEED
            elif delta_x < 0:
                dx = -config.SEEK_SPEED

            if delta_y > 0:
                dy = config.SEEK_SPEED
            elif delta_y < 0:
                dy = -config.SEEK_SPEED
            
            # Avoid getting stuck oscillating over the target if speed > 1
            # If the step would overshoot, just step onto the target coord
            if abs(delta_x) < config.SEEK_SPEED:
                dx = delta_x
            if abs(delta_y) < config.SEEK_SPEED:
                dy = delta_y

        else:
            # Wander randomly
            dx = random.choice([-config.GRID_STEP, 0, config.GRID_STEP])
            dy = random.choice([-config.GRID_STEP, 0, config.GRID_STEP])

        # Apply movement and clamp to boundaries
        new_x = _clamp(self.x + dx, 0, world.width - config.BLOB_SIZE)
        new_y = _clamp(self.y + dy, 0, world.height - config.BLOB_SIZE)

        # Ensure movement aligns to grid if wandering or seeking
        # (Seeking speed is set to grid step for phase 2)
        self.x = (new_x // config.GRID_STEP) * config.GRID_STEP
        self.y = (new_y // config.GRID_STEP) * config.GRID_STEP

    def draw(self) -> None:
        """Draws the blob as a simple rectangle."""
        if self.alive:
            # Calculate left and bottom from center
            center_x = self.x + config.BLOB_SIZE / 2
            center_y = self.y + config.BLOB_SIZE / 2
            left = center_x - config.BLOB_SIZE / 2
            bottom = center_y - config.BLOB_SIZE / 2
            arcade.draw.draw_lbwh_rectangle_filled( # Use lbwh
                left,
                bottom,
                config.BLOB_SIZE,
                config.BLOB_SIZE,
                self.color
            )