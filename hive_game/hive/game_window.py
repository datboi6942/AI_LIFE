from __future__ import annotations

import random
from typing import List

import arcade

from hive_game.hive import config
from hive_game.hive.blob import Blob
from hive_game.hive.world import World, ResourceType

class GameWindow(arcade.Window):
    """Main application window for the HiveLife simulation."""

    def __init__(self):
        """Initializes the game window, world, and blobs."""
        super().__init__(
            width=config.WINDOW_WIDTH,
            height=config.WINDOW_HEIGHT,
            title=config.WINDOW_TITLE,
            update_rate=1/config.TICK_RATE_HZ,
            resizable=False
        )
        arcade.set_background_color(config.BACKGROUND_COLOR)

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
            start_x=10,
            start_y=config.WINDOW_HEIGHT - 20,
            color=arcade.color.WHITE,
            font_size=12
        )
        self.blob_count_text = arcade.Text(
            text=f"Blobs: {len(self.blobs)}",
            start_x=10,
            start_y=config.WINDOW_HEIGHT - 40,
            color=arcade.color.WHITE,
            font_size=12
        )

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
        self.fps_text.text = f"FPS: {int(arcade.get_fps())}"
        self.blob_count_text.text = f"Blobs: {live_blobs}"

    def on_draw(self) -> None:
        """Renders the game screen."""
        self.clear()

        # Draw resources
        # Create shape lists on the fly for Phase 1 simplicity
        # For many resources, pre-calculating or using sprite lists is better
        food_shapes = arcade.ShapeElementList()
        water_shapes = arcade.ShapeElementList()

        for (x, y), resource_type in self.world.tiles.items():
            center_x = x + config.BLOB_SIZE / 2
            center_y = y + config.BLOB_SIZE / 2
            if resource_type == ResourceType.FOOD:
                shape = arcade.create_rectangle_filled(
                    center_x, center_y, config.BLOB_SIZE, config.BLOB_SIZE, arcade.color.APPLE_GREEN
                )
                food_shapes.append(shape)
            elif resource_type == ResourceType.WATER:
                shape = arcade.create_rectangle_filled(
                    center_x, center_y, config.BLOB_SIZE, config.BLOB_SIZE, arcade.color.BLUE_SAPPHIRE
                )
                water_shapes.append(shape)

        food_shapes.draw()
        water_shapes.draw()

        # Draw blobs
        for blob in self.blobs:
            blob.draw()

        # Draw HUD
        self.fps_text.draw()
        self.blob_count_text.draw() 