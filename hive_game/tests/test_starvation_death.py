from __future__ import annotations

import pytest

from hive_game.hive import config
from hive_game.hive.blob import Blob
from hive_game.hive.world import World

@pytest.fixture
def dummy_world() -> World:
    """Creates a basic world fixture."""
    return World(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)

def test_blob_dies_from_hunger(dummy_world: World) -> None:
    """Tests if a blob dies when hunger reaches max."""
    blob = Blob(x=10, y=10, hunger=config.BLOB_MAX_NEEDS - 1, thirst=50)
    assert blob.alive

    # One update should push hunger over the edge
    blob.update(dummy_world, 1.0 / config.TICK_RATE_HZ)

    assert not blob.alive
    assert blob.hunger >= config.BLOB_MAX_NEEDS

def test_blob_dies_from_thirst(dummy_world: World) -> None:
    """Tests if a blob dies when thirst reaches max."""
    blob = Blob(x=10, y=10, hunger=50, thirst=config.BLOB_MAX_NEEDS - 1)
    assert blob.alive

    # One update should push thirst over the edge
    blob.update(dummy_world, 1.0 / config.TICK_RATE_HZ)

    assert not blob.alive
    assert blob.thirst >= config.BLOB_MAX_NEEDS

def test_dead_blob_does_not_update(dummy_world: World) -> None:
    """Tests that a dead blob's state does not change."""
    blob = Blob(x=10, y=10, hunger=config.BLOB_MAX_NEEDS, thirst=50)
    blob.alive = False # Mark as dead initially
    initial_x = blob.x
    initial_y = blob.y
    initial_hunger = blob.hunger
    initial_thirst = blob.thirst

    blob.update(dummy_world, 1.0 / config.TICK_RATE_HZ)

    assert not blob.alive
    assert blob.x == initial_x
    assert blob.y == initial_y
    assert blob.hunger == initial_hunger
    assert blob.thirst == initial_thirst 