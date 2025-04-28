from __future__ import annotations

import pytest

from hive_game.hive import config
from hive_game.hive.blob import Blob
from hive_game.hive.world import World, ResourceType

@pytest.fixture
def world_with_both() -> World:
    """Creates a world with food and water at different locations."""
    world = World(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
    world.tiles[(5 * config.GRID_STEP, 5 * config.GRID_STEP)] = ResourceType.FOOD
    world.tiles[(1 * config.GRID_STEP, 1 * config.GRID_STEP)] = ResourceType.WATER
    return world

def test_prioritizes_hunger_when_equal(world_with_both: World) -> None:
    """Tests that food is prioritized when hunger and thirst are equal and high."""
    food_pos = (5 * config.GRID_STEP, 5 * config.GRID_STEP)
    water_pos = (1 * config.GRID_STEP, 1 * config.GRID_STEP)
    blob = Blob(x=3 * config.GRID_STEP, y=3 * config.GRID_STEP, hunger=config.HUNGER_SEEK, thirst=config.THIRST_SEEK)
    blob.last_food_pos = food_pos
    blob.last_water_pos = water_pos

    target = blob._decide_target()
    assert target == food_pos

def test_prioritizes_higher_hunger(world_with_both: World) -> None:
    """Tests that food is prioritized when hunger is higher than thirst (both high)."""
    food_pos = (5 * config.GRID_STEP, 5 * config.GRID_STEP)
    water_pos = (1 * config.GRID_STEP, 1 * config.GRID_STEP)
    blob = Blob(x=3 * config.GRID_STEP, y=3 * config.GRID_STEP, hunger=config.HUNGER_SEEK + 10, thirst=config.THIRST_SEEK)
    blob.last_food_pos = food_pos
    blob.last_water_pos = water_pos

    target = blob._decide_target()
    assert target == food_pos

def test_prioritizes_higher_thirst(world_with_both: World) -> None:
    """Tests that water is prioritized when thirst is higher than hunger (both high)."""
    food_pos = (5 * config.GRID_STEP, 5 * config.GRID_STEP)
    water_pos = (1 * config.GRID_STEP, 1 * config.GRID_STEP)
    blob = Blob(x=3 * config.GRID_STEP, y=3 * config.GRID_STEP, hunger=config.HUNGER_SEEK, thirst=config.THIRST_SEEK + 10)
    blob.last_food_pos = food_pos
    blob.last_water_pos = water_pos

    target = blob._decide_target()
    assert target == water_pos

def test_seeks_food_if_only_hungry(world_with_both: World) -> None:
    """Tests seeking food when only hunger is high."""
    food_pos = (5 * config.GRID_STEP, 5 * config.GRID_STEP)
    water_pos = (1 * config.GRID_STEP, 1 * config.GRID_STEP)
    blob = Blob(x=3 * config.GRID_STEP, y=3 * config.GRID_STEP, hunger=config.HUNGER_SEEK, thirst=config.THIRST_SEEK - 1)
    blob.last_food_pos = food_pos
    blob.last_water_pos = water_pos # Has memory, but not thirsty enough

    target = blob._decide_target()
    assert target == food_pos

def test_seeks_water_if_only_thirsty(world_with_both: World) -> None:
    """Tests seeking water when only thirst is high."""
    food_pos = (5 * config.GRID_STEP, 5 * config.GRID_STEP)
    water_pos = (1 * config.GRID_STEP, 1 * config.GRID_STEP)
    blob = Blob(x=3 * config.GRID_STEP, y=3 * config.GRID_STEP, hunger=config.HUNGER_SEEK - 1, thirst=config.THIRST_SEEK)
    blob.last_food_pos = food_pos # Has memory, but not hungry enough
    blob.last_water_pos = water_pos

    target = blob._decide_target()
    assert target == water_pos 