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
def basic_blob() -> Blob:
    """Creates a basic blob fixture."""
    return Blob(x=10, y=10, hunger=50, thirst=50, energy=50)

def test_needs_increase_over_time(basic_blob: Blob, dummy_world: World) -> None:
    """Tests if hunger and thirst increase over time."""
    initial_hunger = basic_blob.hunger
    initial_thirst = basic_blob.thirst
    # Simulate multiple updates (e.g., 1 second worth)
    for _ in range(config.TICK_RATE_HZ):
        basic_blob.update(dummy_world, 1.0 / config.TICK_RATE_HZ)

    assert basic_blob.hunger > initial_hunger
    assert basic_blob.thirst > initial_thirst
    # Check approximate increase based on rate (allow some tolerance for int conversion)
    expected_hunger = initial_hunger + config.HUNGER_RATE
    expected_thirst = initial_thirst + config.THIRST_RATE
    assert abs(basic_blob.hunger - expected_hunger) <= 1 # Allow tolerance
    assert abs(basic_blob.thirst - expected_thirst) <= 1 # Allow tolerance

def test_needs_capped_at_max(basic_blob: Blob, dummy_world: World) -> None:
    """Tests if needs are capped at BLOB_MAX_NEEDS."""
    basic_blob.hunger = config.BLOB_MAX_NEEDS - 1
    basic_blob.thirst = config.BLOB_MAX_NEEDS - 1

    # Simulate enough updates to exceed max if not capped
    for _ in range(config.TICK_RATE_HZ * 2):
        basic_blob.update(dummy_world, 1.0 / config.TICK_RATE_HZ)
        if not basic_blob.alive: # Blob might die, stop update
            break

    # Even if it died, check the last state before death or current state if alive
    assert basic_blob.hunger <= config.BLOB_MAX_NEEDS
    assert basic_blob.thirst <= config.BLOB_MAX_NEEDS 