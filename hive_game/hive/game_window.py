from __future__ import annotations

import random
from typing import List

import arcade

from hive_game.hive import config
from hive_game.hive.blob import Blob
from hive_game.hive.world import World, ResourceType

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

        self.world = World(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.world.spawn_resources(
            food_n=config.INITIAL_FOOD_COUNT,
            water_n=config.INITIAL_WATER_COUNT
        )

        self.blobs: List[Blob] = []
        for _ in range(config.BLOB_COUNT):
            # Ensure blobs spawn within bounds and on the grid
            max_gx = self.world.grid_width - 1
            max_gy = self.world.grid_height - 1
            spawn_x = random.randint(0, max_gx) * config.GRID_STEP
            spawn_y = random.randint(0, max_gy) * config.GRID_STEP
            self.blobs.append(Blob(x=spawn_x, y=spawn_y))

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
        ) if not headless else None # Don't create text if headless

    def on_update(self, delta_time: float) -> None:
        """Game logic and movement updates.

        Args:
            delta_time: Time interval since the last update.
        """
        live_blobs = 0
        for blob in self.blobs:
            blob.update(self.world, delta_time)
            if blob.alive:
                live_blobs += 1

        # Update HUD
        if not self._headless:
            # Avoid calls to arcade.get_fps() in headless mode
            self.fps_text.text = f"FPS: {int(arcade.get_fps())}"
            self.blob_count_text.text = f"Blobs: {live_blobs}"

    def _update_only(self, delta_time: float) -> None:
        """Runs only the core update logic without HUD updates. For benchmarking."""
        live_blobs = 0 # Keep track even if not displayed
        for blob in self.blobs:
            blob.update(self.world, delta_time)
            if blob.alive:
                live_blobs += 1
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
        self.fps_text.draw()
        self.blob_count_text.draw() 