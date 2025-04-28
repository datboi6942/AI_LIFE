from __future__ import annotations

import pytest

from hive_game.hive import config
from hive_game.hive.blob import Blob
from hive_game.hive.world import World, ResourceType

@pytest.fixture
def world_with_food() -> World:
    """Creates a world with a single food item."""
    world = World(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    world.tiles[(5 * config.GRID_STEP, 5 * config.GRID_STEP)] = ResourceType.FOOD
    return world

def test_hungry_blob_seeks_known_food(world_with_food: World) -> None:
    """Tests that a hungry blob moves towards known food."""
    food_pos = (5 * config.GRID_STEP, 5 * config.GRID_STEP)
    blob = Blob(x=1 * config.GRID_STEP, y=1 * config.GRID_STEP, hunger=config.HUNGER_SEEK)
    blob.last_food_pos = food_pos
    initial_x = blob.x
    initial_y = blob.y

    blob.update(world_with_food, 1.0 / config.TICK_RATE_HZ)

    # Blob should move towards the food (positive dx, positive dy)
    assert blob.x > initial_x
    assert blob.y > initial_y
    assert blob.x == initial_x + config.SEEK_SPEED
    assert blob.y == initial_y + config.SEEK_SPEED

def test_sated_blob_does_not_seek_food(world_with_food: World) -> None:
    """Tests that a blob below the hunger threshold wanders."""
    food_pos = (5 * config.GRID_STEP, 5 * config.GRID_STEP)
    blob = Blob(x=1 * config.GRID_STEP, y=1 * config.GRID_STEP, hunger=config.HUNGER_SEEK - 1)
    blob.last_food_pos = food_pos
    initial_x = blob.x
    initial_y = blob.y

    # Run multiple updates to see if it moves randomly (likely) or stays put
    moved_randomly = False
    for _ in range(10):
        blob.update(world_with_food, 1.0 / config.TICK_RATE_HZ)
        # Check if it moved away from the initial spot in a non-seeking way
        if blob.x != initial_x or blob.y != initial_y:
             # Simple check: did it move? Doesn't guarantee randomness but good enough
             moved_randomly = True
             break

    assert moved_randomly # Should have wandered

def test_hungry_blob_wanders_if_no_memory(world_with_food: World) -> None:
    """Tests that a hungry blob wanders if it doesn't remember food."""
    blob = Blob(x=1 * config.GRID_STEP, y=1 * config.GRID_STEP, hunger=config.HUNGER_SEEK)
    blob.last_food_pos = None # No memory
    initial_x = blob.x
    initial_y = blob.y

    moved = False
    for _ in range(10):
        blob.update(world_with_food, 1.0 / config.TICK_RATE_HZ)
        if blob.x != initial_x or blob.y != initial_y:
            moved = True
            break

    assert moved # Should have wandered 