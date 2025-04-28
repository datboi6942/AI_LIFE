from __future__ import annotations

import pytest
import time # For simulating time passing

from hive_game.hive import config
from hive_game.hive.blob import Blob
from hive_game.hive.world import World, ResourceType

@pytest.fixture
def world_with_resources() -> World:
    """Creates a world with food and water."""
    world = World(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    world.tiles[(5 * config.GRID_STEP, 5 * config.GRID_STEP)] = ResourceType.FOOD
    world.tiles[(1 * config.GRID_STEP, 1 * config.GRID_STEP)] = ResourceType.WATER
    return world

def test_memory_decays_after_time(world_with_resources: World) -> None:
    """Tests that memories expire after MEMORY_SPAN_S."""
    food_pos = (5 * config.GRID_STEP, 5 * config.GRID_STEP)
    water_pos = (1 * config.GRID_STEP, 1 * config.GRID_STEP)
    blob = Blob(x=3 * config.GRID_STEP, y=3 * config.GRID_STEP)

    # Simulate finding resources
    blob.last_food_pos = food_pos
    blob.food_mem_age = 0.0
    blob.last_water_pos = water_pos
    blob.water_mem_age = 0.0

    # Simulate time passing just under the limit
    dt = config.MEMORY_SPAN_S / 2.0
    blob._decay_mem(dt, world_with_resources)
    blob._decay_mem(dt, world_with_resources) # Total time = MEMORY_SPAN_S
    assert blob.last_food_pos == food_pos
    assert blob.last_water_pos == water_pos

    # Simulate one more small step over the limit
    blob._decay_mem(0.1, world_with_resources)
    assert blob.last_food_pos is None
    assert blob.last_water_pos is None

def test_memory_invalidated_if_resource_gone(world_with_resources: World) -> None:
    """Tests that memory is cleared if the resource at the location disappears."""
    food_pos = (5 * config.GRID_STEP, 5 * config.GRID_STEP)
    blob = Blob(x=3 * config.GRID_STEP, y=3 * config.GRID_STEP)

    # Simulate finding food
    blob.last_food_pos = food_pos
    blob.food_mem_age = 0.0
    assert world_with_resources.tile_is_food(*food_pos)

    # Simulate short time passing (memory should still be valid time-wise)
    blob._decay_mem(1.0, world_with_resources)
    assert blob.last_food_pos == food_pos

    # Remove the food from the world
    world_with_resources.consume_tile(*food_pos)
    assert world_with_resources.tile_is_empty(*food_pos)

    # Simulate another short time passing - decay should now invalidate the memory
    blob._decay_mem(1.0, world_with_resources)
    assert blob.last_food_pos is None

def test_eating_resets_memory_age(world_with_resources: World) -> None:
    """Tests that consuming a resource resets the memory age for that resource."""
    food_pos = (5 * config.GRID_STEP, 5 * config.GRID_STEP)
    blob = Blob(x=food_pos[0], y=food_pos[1]) # Start on the food

    # Simulate having an old memory but then finding food again
    blob.last_food_pos = food_pos
    blob.food_mem_age = config.MEMORY_SPAN_S - 1.0 # Almost expired

    # Update should consume the food and reset the memory age
    blob.update(world_with_resources, 1.0 / config.TICK_RATE_HZ)

    assert blob.last_food_pos == food_pos # Memory location should be updated/retained
    assert blob.food_mem_age == 0.0 # Age should be reset
    assert world_with_resources.tile_is_empty(*food_pos) # Food should be gone 