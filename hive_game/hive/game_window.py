from __future__ import annotations

import random
import logging
from typing import List, Tuple, Any, Set, Optional
import time

import arcade

from hive_game.hive import config
from hive_game.hive.blob import Blob
from hive_game.hive.world import World, ResourceType
from hive_game.hive.sound import cleanup_temp_files
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

        for i in range(config.BLOB_COUNT):
            # Ensure blobs spawn within bounds and on the grid
            max_gx = self.world.grid_width - 1
            max_gy = self.world.grid_height - 1
            spawn_x = random.randint(0, max_gx) * config.GRID_STEP
            spawn_y = random.randint(0, max_gy) * config.GRID_STEP
            self.blobs.append(Blob(id=i, x=spawn_x, y=spawn_y, game_window_ref=self))

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

        # Draw HUD
        if not self._headless:
            if self.fps_text:
                self.fps_text.draw()
            if self.blob_count_text:
                self.blob_count_text.draw() 

    def on_close(self) -> None:
        """Called when the window is being closed."""
        # Clean up temporary sound files
        cleanup_temp_files()
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