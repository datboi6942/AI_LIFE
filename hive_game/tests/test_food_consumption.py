from __future__ import annotations

import pytest

from hive_game.hive import config
from hive_game.hive.blob import Blob
from hive_game.hive.world import World, ResourceType

@pytest.fixture
def world_with_resources() -> World:
    """Creates a world with food and water at specific locations."""
    world = World(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    # Place resources aligned to grid
    world.tiles[(1 * config.GRID_STEP, 1 * config.GRID_STEP)] = ResourceType.FOOD
    world.tiles[(2 * config.GRID_STEP, 2 * config.GRID_STEP)] = ResourceType.WATER
    return world

def test_blob_eats_food(world_with_resources: World) -> None:
    """Tests if a blob consumes food and its hunger decreases."""
    food_x = 1 * config.GRID_STEP
    food_y = 1 * config.GRID_STEP
    blob = Blob(x=food_x, y=food_y, hunger=150, thirst=50)
    initial_hunger = blob.hunger

    assert world_with_resources.get_tile(food_x, food_y) == ResourceType.FOOD

    blob.update(world_with_resources, 1.0 / config.TICK_RATE_HZ)

    # Need increased slightly, then decreased by FOOD_FILL
    # Approximate check, exact value depends on timing vs rate
    expected_hunger_after_tick = initial_hunger + (config.HUNGER_RATE / config.TICK_RATE_HZ)
    expected_hunger_after_eating = max(0, expected_hunger_after_tick - config.FOOD_FILL)

    assert abs(blob.hunger - int(expected_hunger_after_eating)) <= 1 # Allow tolerance
    assert world_with_resources.get_tile(food_x, food_y) == ResourceType.EMPTY

def test_blob_drinks_water(world_with_resources: World) -> None:
    """Tests if a blob consumes water and its thirst decreases."""
    water_x = 2 * config.GRID_STEP
    water_y = 2 * config.GRID_STEP
    blob = Blob(x=water_x, y=water_y, hunger=50, thirst=150)
    initial_thirst = blob.thirst

    assert world_with_resources.get_tile(water_x, water_y) == ResourceType.WATER

    blob.update(world_with_resources, 1.0 / config.TICK_RATE_HZ)

    # Need increased slightly, then decreased by WATER_FILL
    expected_thirst_after_tick = initial_thirst + (config.THIRST_RATE / config.TICK_RATE_HZ)
    expected_thirst_after_drinking = max(0, expected_thirst_after_tick - config.WATER_FILL)

    assert abs(blob.thirst - int(expected_thirst_after_drinking)) <= 1 # Allow tolerance
    assert world_with_resources.get_tile(water_x, water_y) == ResourceType.EMPTY

def test_consumption_needs_capped_at_zero(world_with_resources: World) -> None:
    """Tests that eating/drinking doesn't result in negative needs."""
    food_x = 1 * config.GRID_STEP
    food_y = 1 * config.GRID_STEP
    blob_eat = Blob(x=food_x, y=food_y, hunger=10) # Low hunger
    blob_eat.update(world_with_resources, 1.0 / config.TICK_RATE_HZ)
    assert blob_eat.hunger >= 0

    water_x = 2 * config.GRID_STEP
    water_y = 2 * config.GRID_STEP
    # Need a fresh world instance as the previous one was modified
    world_fresh = World(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    world_fresh.tiles[(water_x, water_y)] = ResourceType.WATER
    blob_drink = Blob(x=water_x, y=water_y, thirst=10) # Low thirst
    blob_drink.update(world_fresh, 1.0 / config.TICK_RATE_HZ)
    assert blob_drink.thirst >= 0 