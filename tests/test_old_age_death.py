"""Tests for blob death due to old age."""

from __future__ import annotations
import pytest
from unittest.mock import MagicMock

from hive_game.hive.blob import Blob
from hive_game.hive.world import World, ResourceType
from hive_game.hive import config

@pytest.fixture
def mock_game_window():
    """Fixture to create a mock GameWindow."""
    gw = MagicMock()
    gw.world = MagicMock(spec=World)
    gw.world.width = config.WINDOW_WIDTH
    gw.world.height = config.WINDOW_HEIGHT
    gw.world.get_tile.return_value = ResourceType.EMPTY
    gw.world.tiles = {} # Mock the tiles dictionary
    # gw.world.set_tile = MagicMock() # Removed as set_tile is not used
    return gw

def test_old_age_death(mock_game_window, caplog):
    """Verify that a blob dies when its age exceeds the maximum lifespan."""
    # Setup: Create a blob
    blob = Blob(id=0, game_window_ref=mock_game_window, energy=100, hunger=0, thirst=0)
    assert blob.alive

    # Action: Manually set blob.age_ticks beyond the limit
    blob.age_ticks = blob._max_lifespan_ticks

    # Action: Call blob.update() - the check is immediate at the start of update
    dt = 1 / config.TICK_RATE_HZ
    current_tick = blob.age_ticks + 1
    events = []
    blob.update(mock_game_window.world, dt, current_tick, events)

    # Assertion: Check that blob.alive is False
    assert not blob.alive

    # Assertion: Check logs for "died of old_age"
    assert f"Blob {blob.id} died of old_age." in caplog.text

    # Assertion: Check if food was dropped by checking the tiles dictionary
    expected_coord = ((blob.x // config.GRID_STEP) * config.GRID_STEP, (blob.y // config.GRID_STEP) * config.GRID_STEP)
    assert mock_game_window.world.tiles.get(expected_coord) == ResourceType.FOOD 