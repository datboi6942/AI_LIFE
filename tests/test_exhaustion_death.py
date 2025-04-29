"""Tests for blob death due to exhaustion (zero energy)."""

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

def test_exhaustion_death(mock_game_window, caplog):
    """Verify that a blob dies after spending the grace period at zero energy."""
    # Setup: Create a blob
    blob = Blob(id=0, game_window_ref=mock_game_window, energy=0, hunger=0, thirst=0)
    blob._ticks_at_zero_energy = 0 # Ensure counter starts at 0
    assert blob.alive

    # Precompute ticks needed
    grace_ticks = blob._exhaustion_grace_ticks
    dt = 1 / config.TICK_RATE_HZ
    current_tick = 0
    events = []

    # Action: Simulate ticks just under grace period
    for i in range(grace_ticks - 1):
        current_tick += 1
        # Set energy back to 0 in case decay makes it negative (though update clamps)
        blob.energy = 0
        blob.update(mock_game_window.world, dt, current_tick, events)
        # Assertion: Check blob is still alive during grace period
        assert blob.alive
        assert blob._ticks_at_zero_energy == i + 1

    # Assertion: Blob should still be alive just before the last tick
    assert blob.alive
    assert blob._ticks_at_zero_energy == grace_ticks - 1

    # Action: Simulate one more tick (the one that triggers death)
    current_tick += 1
    blob.energy = 0
    blob.update(mock_game_window.world, dt, current_tick, events)

    # Assertion: Check blob is now dead
    assert not blob.alive

    # Assertion: Check logs for "died of exhaustion"
    assert f"Blob {blob.id} died of exhaustion." in caplog.text

    # Assertion: Check if food was dropped by checking the tiles dictionary
    expected_coord = ((blob.x // config.GRID_STEP) * config.GRID_STEP, (blob.y // config.GRID_STEP) * config.GRID_STEP)
    assert mock_game_window.world.tiles.get(expected_coord) == ResourceType.FOOD
 