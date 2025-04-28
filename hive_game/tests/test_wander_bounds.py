from __future__ import annotations

import pytest

from hive_game.hive import config
from hive_game.hive.blob import Blob
from hive_game.hive.world import World

@pytest.fixture
def dummy_world() -> World:
    """Creates a basic world fixture."""
    return World(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)

@pytest.fixture
def blob_at_center(dummy_world: World) -> Blob:
    """Creates a blob near the center of the world."""
    center_x = (dummy_world.width // 2 // config.GRID_STEP) * config.GRID_STEP
    center_y = (dummy_world.height // 2 // config.GRID_STEP) * config.GRID_STEP
    return Blob(x=center_x, y=center_y)

def test_blob_wander_changes_position(blob_at_center: Blob, dummy_world: World) -> None:
    """Tests that wandering actually changes the blob's position over time."""
    initial_x = blob_at_center.x
    initial_y = blob_at_center.y

    # Run update multiple times to increase chance of movement
    moved = False
    for _ in range(10):
        blob_at_center.update(dummy_world, 1.0 / config.TICK_RATE_HZ)
        if blob_at_center.x != initial_x or blob_at_center.y != initial_y:
            moved = True
            break
    assert moved

def test_blob_wander_stays_within_bounds(dummy_world: World) -> None:
    """Tests that wandering blobs do not move outside the world boundaries."""
    # Start blob at edge cases
    blobs = [
        Blob(x=0, y=0), # Top-left
        Blob(x=dummy_world.width - config.BLOB_SIZE, y=0), # Top-right
        Blob(x=0, y=dummy_world.height - config.BLOB_SIZE), # Bottom-left
        Blob(x=dummy_world.width - config.BLOB_SIZE, y=dummy_world.height - config.BLOB_SIZE) # Bottom-right
    ]

    for blob in blobs:
        initial_x = blob.x
        initial_y = blob.y
        # Run update multiple times
        for _ in range(20):
            blob.update(dummy_world, 1.0 / config.TICK_RATE_HZ)
            # Assert bounds after each step
            assert 0 <= blob.x <= dummy_world.width - config.BLOB_SIZE
            assert 0 <= blob.y <= dummy_world.height - config.BLOB_SIZE 