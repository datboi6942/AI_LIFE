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
    vx: int = 0  # Added velocity components
    vy: int = 0
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

    def _wander(self) -> None:
        """Randomly changes direction based on WANDER_RATE."""
        if random.random() < config.WANDER_RATE:
            self.vx = random.choice([-config.GRID_STEP, 0, config.GRID_STEP])
            self.vy = random.choice([-config.GRID_STEP, 0, config.GRID_STEP])

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
        target = self._decide_target()
        if target:
            # Seek target
            target_x, target_y = target
            # Calculate direction vector components
            delta_x = target_x - self.x
            delta_y = target_y - self.y

            # Set velocity based on direction to target
            self.vx = _clamp(delta_x, -config.SEEK_SPEED, config.SEEK_SPEED)
            self.vy = _clamp(delta_y, -config.SEEK_SPEED, config.SEEK_SPEED)
        else:
            # Wander randomly
            self._wander()

        # Apply movement
        self.x += self.vx
        self.y += self.vy

        # Clamp to boundaries
        self.x = _clamp(self.x, 0, world.width - config.BLOB_SIZE)
        self.y = _clamp(self.y, 0, world.height - config.BLOB_SIZE)

        # Ensure movement aligns to grid if wandering or seeking
        # (Seeking speed is set to grid step for phase 2)
        self.x = (self.x // config.GRID_STEP) * config.GRID_STEP
        self.y = (self.y // config.GRID_STEP) * config.GRID_STEP

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

    def draw(self) -> None:
        """Draws the blob as a rounded rectangle."""
        if not self.alive:
            return
            
        # Draw the main body
        arcade.draw.draw_arc_filled(
            self.x + config.BLOB_SIZE/2,  # center x
            self.y + config.BLOB_SIZE/2,  # center y
            config.BLOB_SIZE,  # width
            config.BLOB_SIZE,  # height
            self.color,
            0, 360,  # start and end angles
            8  # number of segments
        )
        
        # Draw a slightly darker outline
        darker_color = tuple(max(0, c - 40) for c in self.color)
        arcade.draw.draw_arc_outline(
            self.x + config.BLOB_SIZE/2,  # center x
            self.y + config.BLOB_SIZE/2,  # center y
            config.BLOB_SIZE,  # width
            config.BLOB_SIZE,  # height
            darker_color,
            0, 360,  # start and end angles
            8,  # number of segments
            2  # line width
        )