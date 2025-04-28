from __future__ import annotations

import pytest

from hive_game.hive import config
from hive_game.hive.blob import Blob
from hive_game.hive.world import World, ResourceType

@pytest.fixture
def world_with_water() -> World:
    """Creates a world with a single water item."""
    world = World(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    world.tiles[(5 * config.GRID_STEP, 5 * config.GRID_STEP)] = ResourceType.WATER
    return world

def test_thirsty_blob_seeks_known_water(world_with_water: World) -> None:
    """Tests that a thirsty blob moves towards known water."""
    water_pos = (5 * config.GRID_STEP, 5 * config.GRID_STEP)
    blob = Blob(x=1 * config.GRID_STEP, y=1 * config.GRID_STEP, thirst=config.THIRST_SEEK)
    blob.last_water_pos = water_pos
    initial_x = blob.x
    initial_y = blob.y

    blob.update(world_with_water, 1.0 / config.TICK_RATE_HZ)

    # Blob should move towards the water (positive dx, positive dy)
    assert blob.x > initial_x
    assert blob.y > initial_y
    assert blob.x == initial_x + config.SEEK_SPEED
    assert blob.y == initial_y + config.SEEK_SPEED

def test_quenched_blob_does_not_seek_water(world_with_water: World) -> None:
    """Tests that a blob below the thirst threshold wanders."""
    water_pos = (5 * config.GRID_STEP, 5 * config.GRID_STEP)
    blob = Blob(x=1 * config.GRID_STEP, y=1 * config.GRID_STEP, thirst=config.THIRST_SEEK - 1)
    blob.last_water_pos = water_pos
    initial_x = blob.x
    initial_y = blob.y

    moved_randomly = False
    for _ in range(10):
        blob.update(world_with_water, 1.0 / config.TICK_RATE_HZ)
        if blob.x != initial_x or blob.y != initial_y:
            moved_randomly = True
            break

    assert moved_randomly # Should have wandered

def test_thirsty_blob_wanders_if_no_memory(world_with_water: World) -> None:
    """Tests that a thirsty blob wanders if it doesn't remember water."""
    blob = Blob(x=1 * config.GRID_STEP, y=1 * config.GRID_STEP, thirst=config.THIRST_SEEK)
    blob.last_water_pos = None # No memory
    initial_x = blob.x
    initial_y = blob.y

    moved = False
    for _ in range(10):
        blob.update(world_with_water, 1.0 / config.TICK_RATE_HZ)
        if blob.x != initial_x or blob.y != initial_y:
            moved = True
            break

    assert moved # Should have wandered 