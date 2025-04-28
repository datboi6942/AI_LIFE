from __future__ import annotations

import random
import logging
from typing import List, Tuple, Any, Set, Optional
import time
import math

import arcade
# Explicitly import drawing functions used
from arcade.draw import draw_lbwh_rectangle_filled

from hive_game.hive import config
from hive_game.hive.blob import Blob
from hive_game.hive.world import World, ResourceType
from hive_game.hive import hive_mind

log = logging.getLogger(__name__)

class GameWindow(arcade.Window):
    """Main application window for the HiveLife simulation."""

    def __init__(self, headless: bool = False):
        """Initializes the game window, world, and blobs.

        Args:
            headless: If True, initializes without creating a visible window.
                      Used for testing/benchmarking.
        """
        self._headless = headless
        if not headless:
            super().__init__(
                width=config.WINDOW_WIDTH,
                height=config.WINDOW_HEIGHT,
                title=config.WINDOW_TITLE,
                update_rate=1/config.TICK_RATE_HZ,
                resizable=False
            )
            self.background_color = config.BACKGROUND_COLOR
        else:
            # Need to initialize some things even without a window
            # Setting a dummy context might be needed for some arcade features,
            # but let's try without it first for simplicity.
            # If tests fail, we might need: arcade.Window.__init__(self, ...) with visible=False
            # For now, just skip super().__init__ and graphics setup.
            pass

        self.current_tick: int = 0
        self.world = World(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.world.spawn_resources(
            food_n=config.INITIAL_FOOD_COUNT,
            water_n=config.INITIAL_WATER_COUNT
        )

        self.blobs: List[Blob] = []
        self.events: List[Tuple[str, Any]] = []
        self.used_chirp_ids: Set[int] = set()
        random.seed(42)
        self._chirp_id_pool = list(range(256))
        random.shuffle(self._chirp_id_pool)
        self._chirp_id_iterator = iter(self._chirp_id_pool)
        self.convergence_log: List[Tuple[int, float]] = []

        # ID Counter - start after initial population
        self.next_blob_id: int = 0

        for i in range(config.BLOB_COUNT):
            # Ensure blobs spawn within bounds and on the grid
            max_gx = self.world.grid_width - 1
            max_gy = self.world.grid_height - 1
            spawn_x = random.randint(0, max_gx) * config.GRID_STEP
            spawn_y = random.randint(0, max_gy) * config.GRID_STEP
            # Use get_next_blob_id for initial population as well
            blob_id = self.get_next_blob_id()
            self.blobs.append(Blob(id=blob_id, x=spawn_x, y=spawn_y, game_window_ref=self))

        # --- Visual Feedback State ---
        self.debug_mode: bool = config.SHOW_DEBUG_DEFAULT
        self._hovered_blob: Optional[Blob] = None # Track blob under mouse

        # --- HUD Initialization (only if not headless) ---
        if not headless:
            self.fps_text = arcade.Text(
                text="FPS: 0",
                x=10,
                y=config.WINDOW_HEIGHT - 20,
                color=arcade.color.WHITE,
                font_size=12
            )
            self.blob_count_text = arcade.Text(
                text=f"Blobs: {len(self.blobs)}",
                x=10,
                y=config.WINDOW_HEIGHT - 40,
                color=arcade.color.WHITE,
                font_size=12
            )
        else:
            # Initialize text attributes to None in headless mode
            self.fps_text = None
            self.blob_count_text = None

    def get_next_blob_id(self) -> int:
        """Returns the next available unique ID for a new blob."""
        next_id = self.next_blob_id
        self.next_blob_id += 1
        return next_id

    def add_blob(self, blob: Blob) -> None:
        """Adds a new blob to the simulation."""
        if len(self.blobs) < config.MAX_BLOBS:
            self.blobs.append(blob)
            log.debug(f"Added offspring blob {blob.id}, population now {len(self.blobs)}")
        else:
            log.debug(f"MAX_BLOBS reached ({config.MAX_BLOBS}), could not add offspring.")
            # Handle the case where offspring cannot be added (optional: log, ignore)
            # Currently, the blob object created by the parent will just be discarded.

    def get_nearby_blobs(self, center_blob: Blob, radius: float) -> List[Blob]:
        """Finds blobs (excluding self) within a given radius."""
        nearby = []
        for other_blob in self.blobs:
            if other_blob.id == center_blob.id or not other_blob.alive:
                continue # Skip self and dead blobs
            
            distance = math.hypot(center_blob.x - other_blob.x, center_blob.y - other_blob.y)
            if distance <= radius:
                nearby.append(other_blob)
        return nearby

    def get_new_chirp_id(self) -> Optional[int]:
        """Gets the next available unique chirp ID from the shuffled pool."""
        try:
            new_id = next(self._chirp_id_iterator)
            while new_id in self.used_chirp_ids:
                log.warning(f"Chirp ID {new_id} already used, getting next...")
                new_id = next(self._chirp_id_iterator)
            self.used_chirp_ids.add(new_id)
            return new_id
        except StopIteration:
            log.error("Ran out of unique chirp IDs in the initial pool!")
            return None

    def on_key_press(self, key, modifiers):
        """Handle keyboard events."""
        if key == arcade.key.F2:
            self.debug_mode = not self.debug_mode
            log.info(f"Debug mode {'enabled' if self.debug_mode else 'disabled'}")
        # Add other key handlers here if needed

    def on_mouse_motion(self, x, y, dx, dy):
        """Update hovered blob when mouse moves (only if debug mode is on)."""
        if self.debug_mode:
            self._hovered_blob = self._find_blob_at(x, y)

    def _find_blob_at(self, x: int, y: int) -> Optional[Blob]:
        """Finds the topmost blob whose bounding box contains the coordinates."""
        closest_blob = None
        min_dist_sq = float('inf')

        for blob in reversed(self.blobs): # Check topmost first
            if not blob.alive:
                continue
            # Simple bounding box check
            blob_right = blob.x + config.BLOB_SIZE
            blob_top = blob.y + config.BLOB_SIZE
            if blob.x <= x < blob_right and blob.y <= y < blob_top:
                # Optional: Use distance if point is inside multiple overlapping blobs
                # dist_sq = (blob.x + config.BLOB_SIZE/2 - x)**2 + (blob.y + config.BLOB_SIZE/2 - y)**2
                # if dist_sq < min_dist_sq:
                #     min_dist_sq = dist_sq
                #     closest_blob = blob
                return blob # Return the first one found (topmost)
        return None

    def on_update(self, delta_time: float) -> None:
        """Game logic and movement updates.

        Args:
            delta_time: Time interval since the last update.
        """
        self.current_tick += 1
        self.events.clear()

        live_blobs = 0
        for blob in self.blobs:
            if blob.alive:
                blob.update(self.world, delta_time, self.current_tick, self.events)
                live_blobs += 1

        # Filter out dead blobs
        self.blobs = [blob for blob in self.blobs if blob.alive]

        # --- Regenerate World Resources ---
        regen_interval_ticks = int(config.RESOURCE_REGEN_INTERVAL_S * config.TICK_RATE_HZ)
        if regen_interval_ticks > 0 and self.current_tick % regen_interval_ticks == 0:
            self.world.tick_regen() # Assuming this method exists

        # Restore convergence logic
        convergence_result = hive_mind.update_convergence(
            [b for b in self.blobs if b.alive],
            self.current_tick,
            config.CONVERGENCE_INTERVAL
        )
        if convergence_result is not None:
            self.convergence_log.append((self.current_tick, convergence_result))
            # Log convergence status (adjust conditions as needed)
            if self.current_tick % (config.TICK_RATE_HZ * 10) == 0: # Log every 10s
                 log.info(f"Tick {self.current_tick}: Convergence Jaccard = {convergence_result:.3f}")

        # Update HUD
        if not self._headless:
            # Safely access text objects only if they exist
            if self.fps_text:
                self.fps_text.text = f"FPS: {int(arcade.get_fps())}"
            if self.blob_count_text:
                self.blob_count_text.text = f"Blobs: {live_blobs}"

    def _update_only(self, delta_time: float) -> None:
        """Runs only the core update logic without HUD updates. For benchmarking."""
        self.current_tick += 1
        self.events.clear()

        live_blobs = 0 # Keep track even if not displayed
        for blob in self.blobs:
            if blob.alive:
                blob.update(self.world, delta_time, self.current_tick, self.events)
                live_blobs += 1

        # Filter out dead blobs
        self.blobs = [blob for blob in self.blobs if blob.alive]

        # --- Regenerate World Resources ---
        regen_interval_ticks = int(config.RESOURCE_REGEN_INTERVAL_S * config.TICK_RATE_HZ)
        if regen_interval_ticks > 0 and self.current_tick % regen_interval_ticks == 0:
            self.world.tick_regen() # Assuming this method exists

        # Restore convergence logic (no logging needed in benchmark mode)
        _ = hive_mind.update_convergence(
            [b for b in self.blobs if b.alive],
            self.current_tick,
            config.CONVERGENCE_INTERVAL
        )
        # No HUD update here

    def on_draw(self) -> None:
        """Renders the game screen."""
        if self._headless:
            return # Don't draw in headless mode

        self.clear()

        # --- Draw resources (individual draw calls) ---
        resource_width = config.BLOB_SIZE
        resource_height = config.BLOB_SIZE
        food_color = arcade.color.APPLE_GREEN
        water_color = arcade.color.BLUE_SAPPHIRE

        for (x, y), resource_type in self.world.tiles.items():
            center_x = x + resource_width / 2
            center_y = y + resource_height / 2
            if resource_type == ResourceType.FOOD:
                # Calculate left and bottom from center
                left = center_x - resource_width / 2
                bottom = center_y - resource_height / 2
                arcade.draw.draw_lbwh_rectangle_filled( # Use lbwh
                    left,
                    bottom,
                    resource_width,
                    resource_height,
                    food_color
                )
            elif resource_type == ResourceType.WATER:
                 # Calculate left and bottom from center
                 left = center_x - resource_width / 2
                 bottom = center_y - resource_height / 2
                 arcade.draw.draw_lbwh_rectangle_filled( # Use lbwh
                    left,
                    bottom,
                    resource_width,
                    resource_height,
                    water_color
                )
        # --- End resource drawing ---

        # Draw blobs
        for blob in self.blobs:
            blob.draw()

        # --- Draw Action Bubbles ---
        for blob in self.blobs:
            if blob.alive and blob.last_emit_concept is not None:
                ticks_since_emit = self.current_tick - blob.last_emit_tick
                if ticks_since_emit <= config.BUBBLE_DURATION_TICKS:
                    self._draw_bubble(blob)

        # --- Draw Debug Panel (if active and blob hovered) ---
        if self.debug_mode and self._hovered_blob:
            self._draw_debug_panel(self._hovered_blob)

        # Draw HUD
        if not self._headless:
            if self.fps_text:
                self.fps_text.draw()
            if self.blob_count_text:
                self.blob_count_text.draw()

    def _draw_bubble(self, blob: Blob) -> None:
        """Draws a small indicator bubble above the blob."""
        bubble_size = 10
        bubble_x = blob.x + config.BLOB_SIZE / 2 # Center horizontally
        bubble_y = blob.y + config.BLOB_SIZE + config.BUBBLE_OFFSET_PX # Position above

        # Icon based on concept
        icon_color = arcade.color.DARK_GRAY # Default if concept unknown
        if blob.last_emit_concept == "food":
            icon_color = arcade.color.APPLE_GREEN
        elif blob.last_emit_concept == "water":
            icon_color = arcade.color.BLUE_SAPPHIRE

        # Calculate L, B from Center X, Y for draw_lbwh
        rect_width = bubble_size * 0.8
        rect_height = bubble_size * 0.8
        center_x = bubble_x
        center_y = bubble_y + bubble_size / 2
        left = center_x - rect_width / 2
        bottom = center_y - rect_height / 2

        draw_lbwh_rectangle_filled(left, bottom, # Use calculated L, B
                                          rect_width, rect_height, # Slightly smaller icon
                                          icon_color)

    def _draw_debug_panel(self, blob: Blob) -> None:
        """Draws the debug information panel for the hovered blob."""
        panel_x = 10
        panel_y = config.WINDOW_HEIGHT - 70 # Position below existing HUD
        panel_width = 200
        panel_height = 100
        bg_color = arcade.make_transparent_color(arcade.color.BLACK, alpha=180)
        text_color = arcade.color.WHITE_SMOKE
        font_size = 9
        line_height = 12

        # Draw background
        # Calculate L, B from Center X, Y for draw_lbwh
        center_x = panel_x + panel_width / 2
        center_y = panel_y - panel_height / 2
        left = center_x - panel_width / 2
        bottom = center_y - panel_height / 2

        draw_lbwh_rectangle_filled(left, bottom, # Use calculated L, B
                                          panel_width, panel_height, bg_color)

        # Prepare text lines
        lines = [
            f"ID: {blob.id}",
            f"Hunger: {blob.hunger} / {config.BLOB_MAX_NEEDS}",
            f"Thirst: {blob.thirst} / {config.BLOB_MAX_NEEDS}",
            f"Energy: {blob.energy}",
        ]

        # Target
        target = blob._decide_target()
        target_str = "Wandering"
        if target:
            target_type = "UNKNOWN"
            if blob.last_food_pos == target:
                target_type = "FOOD"
            elif blob.last_water_pos == target:
                target_type = "WATER"
            target_str = f"Target: {target_type} ({target[0]},{target[1]})"
        lines.append(target_str)

        # Lexicon (Top 3)
        lex_str = "Lexicon: "
        if blob.lexicon:
            # Sort lexicon items by weight descending for each concept
            sorted_lex = []
            for chirp_id, concepts in blob.lexicon.items():
                for concept, weight in concepts.items():
                    sorted_lex.append((weight, chirp_id, concept))
            
            sorted_lex.sort(reverse=True)
            lex_items = [f"{cid}▶{con}({w:.2f})" for w, cid, con in sorted_lex[:3]]
            lex_str += "  ".join(lex_items)
        else:
            lex_str += "(Empty)"
        lines.append(lex_str)

        # Draw text lines
        start_y = panel_y - line_height
        for i, line in enumerate(lines):
            arcade.draw_text(line, panel_x + 5, start_y - i * line_height, # Call using arcade.* namespace
                                text_color, font_size=font_size)

    def on_close(self) -> None:
        """Called when the window is being closed."""
        # Save convergence data if needed
        if self.convergence_log:
             log.info(f"Saving convergence log with {len(self.convergence_log)} entries.")
             # Implement saving logic here (e.g., to CSV or JSON)
             # Example:
             # import csv
             # with open("convergence_log.csv", "w", newline="") as f:
             #     writer = csv.writer(f)
             #     writer.writerow(["tick", "jaccard_index"])
             #     writer.writerows(self.convergence_log)

        super().on_close() 