from __future__ import annotations

import random
import uuid
import math # Added for distance calculation
import logging # Added for logging
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, List, Any, TYPE_CHECKING # Added Dict, List, Any, TYPE_CHECKING

import arcade

from hive_game.hive import config
from hive_game.hive.world import World, ResourceType
from hive_game.hive import sound # Added sound import

if TYPE_CHECKING:
    from hive_game.hive.game_window import GameWindow # Import GameWindow for type hinting

def _clamp(value: float | int, low: float | int, high: float | int) -> float | int:
    """Clamps a numeric value between low and high."""
    return max(low, min(value, high))

@dataclass
class Blob:
    """Represents a single blob creature in the simulation."""

    # Non-default fields first
    id: int
    game_window_ref: "GameWindow" = field(repr=False) # Reference to access global state

    # Default fields next
    x: int = 0
    y: int = 0
    vx: int = 0
    vy: int = 0
    color: tuple[int, int, int] = field(default_factory=lambda: random.choice([
        arcade.color.RED,
        arcade.color.BLUE,
        arcade.color.GREEN,
        arcade.color.YELLOW,
        arcade.color.PURPLE,
        arcade.color.ORANGE
    ]))
    hunger: int = 0
    thirst: int = 0
    energy: int = 100
    alive: bool = True

    # --- Phase 2 Memory ---
    last_food_pos: Optional[Tuple[int, int]] = None
    last_water_pos: Optional[Tuple[int, int]] = None
    food_mem_age: float = 0.0
    water_mem_age: float = 0.0

    # --- Phase 3 Communication & Learning ---
    lexicon: Dict[int, Dict[str, float]] = field(default_factory=dict)
    heard_chirps_pending_reinforcement: List[Tuple[int, str, int]] = field(default_factory=list)
    last_chirp_time: float = -1.0
    _chirp_cooldown: float = 0.5
    _reinforcement_delay_ticks: int = 180

    # Internal derived rates (have defaults essentially)
    _hunger_rate_tick: float = config.HUNGER_RATE / config.TICK_RATE_HZ
    _thirst_rate_tick: float = config.THIRST_RATE / config.TICK_RATE_HZ
    _energy_decay_tick: float = config.ENERGY_DECAY / config.TICK_RATE_HZ

    def _wander(self) -> None:
        """Randomly changes direction based on WANDER_RATE."""
        if random.random() < config.WANDER_RATE:
            self.vx = random.choice([-config.GRID_STEP, 0, config.GRID_STEP])
            self.vy = random.choice([-config.GRID_STEP, 0, config.GRID_STEP])

    def update(self, world: World, dt: float, current_tick: int, events: List[Tuple[str, Any]]) -> None:
        """Updates the blob's state for one tick.

        Args:
            world: The world object containing resource information.
            dt: Delta time since the last update.
            current_tick: The current simulation tick count.
            events: The global event queue for this frame.
        """
        if not self.alive:
            return

        # --- Phase 3: Process Heard Chirps (from previous frame's events) ---
        self._process_heard_chirps(events, current_tick)

        # --- Phase 3: Process Pending Reinforcements ---
        self._process_reinforcement_queue(current_tick)

        # --- Phase 3: Lexicon Decay ---
        self._decay_lexicon(dt)

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

        # --- Check for Resources at Current Location & Update Memory/Learning ---
        current_tile_type = world.get_tile(self.x, self.y)
        consumed_concept = None
        if current_tile_type == ResourceType.FOOD:
            self.hunger = max(0, self.hunger - config.FOOD_FILL)
            self.last_food_pos = (self.x, self.y) # Store current pos
            self.food_mem_age = 0.0 # Reset age
            world.consume_tile(self.x, self.y)
            consumed_concept = "food"
        elif current_tile_type == ResourceType.WATER:
            self.thirst = max(0, self.thirst - config.WATER_FILL)
            self.last_water_pos = (self.x, self.y) # Store current pos
            self.water_mem_age = 0.0 # Reset age
            world.consume_tile(self.x, self.y)
            consumed_concept = "water"

        if consumed_concept:
            # --- Phase 3: Positive Reinforcement & Broadcast ---
            self._apply_positive_reinforcement(consumed_concept)
            self._broadcast_discovery(consumed_concept, current_tick, events)

        # --- Movement (Seeking or Wandering) ---
        target = self._decide_target()
        if target:
            # Seek target
            target_x, target_y = target
            # Calculate direction vector components (simple difference)
            delta_x = target_x - self.x
            delta_y = target_y - self.y

            # Set velocity based on direction to target, clamped by SEEK_SPEED
            # If delta is small, step directly onto target to avoid oscillation
            self.vx = _clamp(delta_x, -config.SEEK_SPEED, config.SEEK_SPEED)
            self.vy = _clamp(delta_y, -config.SEEK_SPEED, config.SEEK_SPEED)
            if abs(delta_x) <= config.SEEK_SPEED: self.vx = delta_x
            if abs(delta_y) <= config.SEEK_SPEED: self.vy = delta_y

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
        """Decides the target coordinates based on needs and memory.

        Returns:
            A tuple (x, y) of the target coordinates, or None if wandering.
        """
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

    # --- Phase 3 Methods --- 

    def _get_dominant_chirp_for_concept(self, concept: str) -> Optional[int]:
        """Finds a chirp ID strongly associated (>0.5) with the concept."""
        best_id = None
        max_weight = 0.5 # Threshold
        for chirp_id, concepts in self.lexicon.items():
            weight = concepts.get(concept, 0.0)
            if weight > max_weight:
                max_weight = weight
                best_id = chirp_id
        return best_id

    def _allocate_new_chirp_id(self, concept: str) -> Optional[int]:
        """Requests a new chirp ID from the GameWindow and initializes lexicon entry."""
        new_id = self.game_window_ref.get_new_chirp_id()
        if new_id is not None:
            self.lexicon.setdefault(new_id, {})[concept] = 0.2 # Initial weight
            logging.debug(f"Blob {self.id} allocated new chirp ID {new_id} for concept '{concept}'")
        return new_id

    def _broadcast_discovery(self, concept: str, current_tick: int, events: List[Tuple[str, Any]]) -> None:
        """Emits a chirp associated with the discovered resource concept."""
        current_time = current_tick / config.TICK_RATE_HZ
        if current_time - self.last_chirp_time < self._chirp_cooldown:
            return # Rate limit self

        chirp_id = self._get_dominant_chirp_for_concept(concept)
        if chirp_id is None:
            chirp_id = self._allocate_new_chirp_id(concept)

        if chirp_id is not None:
            # Check global rate limit (CHIRP_VOLUME)
            # Count existing chirp events already added this frame
            chirp_event_count = sum(1 for event in events if event[0] == "chirp")
            if chirp_event_count < config.CHIRP_VOLUME:
                event = ("chirp", self.id, chirp_id, self.x, self.y)
                events.append(event)
                sound.play_chirp(chirp_id, self.game_window_ref)
                self.last_chirp_time = current_time
                logging.debug(f"Blob {self.id} broadcast chirp {chirp_id} for {concept} at ({self.x}, {self.y})")
            else:
                logging.debug(f"Chirp volume limit reached, Blob {self.id} could not chirp.")

    def _process_heard_chirps(self, events: List[Tuple[str, Any]], current_tick: int) -> None:
        """Processes chirp events from the global queue, adding potential reinforcements."""
        for event_type, *data in events:
            if event_type == "chirp":
                emitter_id, chirp_id, x, y = data
                if emitter_id == self.id:
                    continue # Don't hear self

                distance = math.hypot(self.x - x, self.y - y)
                if distance < config.CHIRP_RADIUS:
                    # Determine concept guess based on strongest need
                    concept_guess = None
                    is_hungry = self.hunger >= config.HUNGER_SEEK
                    is_thirsty = self.thirst >= config.THIRST_SEEK
                    if is_hungry and is_thirsty:
                        concept_guess = "food" if self.hunger >= self.thirst else "water"
                    elif is_hungry:
                        concept_guess = "food"
                    elif is_thirsty:
                        concept_guess = "water"

                    if concept_guess:
                        expiry = current_tick + self._reinforcement_delay_ticks
                        self.heard_chirps_pending_reinforcement.append((chirp_id, concept_guess, expiry))
                        logging.debug(f"Blob {self.id} heard chirp {chirp_id}, expecting {concept_guess}, expiry {expiry}")

    def _apply_positive_reinforcement(self, consumed_concept: str) -> None:
        """Applies positive reinforcement to lexicon for recently heard chirps matching the outcome."""
        items_to_remove = []
        for i, (chirp_id, concept_guess, expiry_tick) in enumerate(self.heard_chirps_pending_reinforcement):
            if concept_guess == consumed_concept:
                current_weight = self.lexicon.setdefault(chirp_id, {}).get(concept_guess, 0.0)
                new_weight = min(1.0, current_weight + 0.2)
                self.lexicon[chirp_id][concept_guess] = new_weight
                items_to_remove.append(i)
                logging.debug(f"Blob {self.id}: Positive reinforcement for chirp {chirp_id}/{concept_guess}, new weight {new_weight:.2f}")

        # Remove processed items (iterate backwards to avoid index issues)
        for i in sorted(items_to_remove, reverse=True):
            del self.heard_chirps_pending_reinforcement[i]

    def _process_reinforcement_queue(self, current_tick: int) -> None:
        """Processes the pending reinforcement queue for expirations (negative reinforcement)."""
        items_to_remove = []
        for i, (chirp_id, concept_guess, expiry_tick) in enumerate(self.heard_chirps_pending_reinforcement):
            if current_tick >= expiry_tick:
                # Expectation expired without positive reinforcement, apply negative
                current_weight = self.lexicon.setdefault(chirp_id, {}).get(concept_guess, 0.0)
                new_weight = max(0.0, current_weight - 0.05)
                self.lexicon[chirp_id][concept_guess] = new_weight
                items_to_remove.append(i)
                logging.debug(f"Blob {self.id}: Negative reinforcement for chirp {chirp_id}/{concept_guess}, new weight {new_weight:.2f}")

        # Remove processed items (iterate backwards)
        for i in sorted(items_to_remove, reverse=True):
            del self.heard_chirps_pending_reinforcement[i]

    def _decay_lexicon(self, dt: float) -> None:
        """Applies decay to all weights in the lexicon."""
        decay_factor = (1.0 - config.LEXICON_DECAY * dt)
        # Iterate carefully, potentially removing entries if weight is near zero
        chirp_ids_to_check = list(self.lexicon.keys())
        for chirp_id in chirp_ids_to_check:
            concepts_to_check = list(self.lexicon[chirp_id].keys())
            for concept in concepts_to_check:
                self.lexicon[chirp_id][concept] *= decay_factor
                # Optional: Clean up very small weights to prevent dict bloat
                if self.lexicon[chirp_id][concept] < 0.001:
                     del self.lexicon[chirp_id][concept]
            # Optional: Clean up chirp_id entry if no concepts remain
            if not self.lexicon[chirp_id]:
                del self.lexicon[chirp_id]

    # --- End Phase 3 Methods ---