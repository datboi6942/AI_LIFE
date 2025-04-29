"""Tests for successful blob reproduction."""

from __future__ import annotations
import pytest
from unittest.mock import MagicMock

from hive_game.hive.blob import Blob
from hive_game.hive.world import World, ResourceType
from hive_game.hive import config

@pytest.fixture
def mock_game_window():
    """Fixture to create a mock GameWindow with necessary methods."""
    gw = MagicMock()
    gw.blobs = [] # List to hold blobs managed by the mock GameWindow
    gw._next_blob_id = 2 # Start IDs after parents
    gw.world = MagicMock(spec=World)
    gw.world.width = config.WINDOW_WIDTH
    gw.world.height = config.WINDOW_HEIGHT
    gw.world.get_tile.return_value = ResourceType.EMPTY # Default empty world

    def add_blob(blob):
        gw.blobs.append(blob)

    def get_nearby_blobs(blob, radius):
        # Simple mock: return other blobs if they exist and are close enough
        # In this test, parents are at the same spot, so they find each other.
        return [b for b in gw.blobs if b.id != blob.id and abs(b.x - blob.x) < radius and abs(b.y - blob.y) < radius]

    def get_next_blob_id():
        id = gw._next_blob_id
        gw._next_blob_id += 1
        return id

    gw.add_blob.side_effect = add_blob
    gw.get_nearby_blobs.side_effect = get_nearby_blobs
    gw.get_next_blob_id.side_effect = get_next_blob_id
    return gw

def test_reproduction_success(mock_game_window, caplog):
    """Verify that two eligible blobs reproduce successfully."""
    # Setup: Create two parent blobs meeting criteria
    parent_a_start_energy = config.REPRO_ENERGY_THRESH + 10
    parent_b_start_energy = config.REPRO_ENERGY_THRESH + 20
    current_tick = 10_000 # Ensure cooldown is not an issue initially

    parent_a = Blob(
        id=0,
        game_window_ref=mock_game_window,
        x=100, y=100,
        energy=parent_a_start_energy,
        hunger=0, thirst=0,
        last_repro_tick=0 # Ready to reproduce
    )
    parent_b = Blob(
        id=1,
        game_window_ref=mock_game_window,
        x=100, y=100, # Same location for simplicity
        energy=parent_b_start_energy,
        hunger=0, thirst=0,
        last_repro_tick=0 # Ready to reproduce
    )

    mock_game_window.blobs = [parent_a, parent_b] # Add parents to the mock list

    # Action: Advance simulation tick for parent A (triggers check)
    dt = 1 / config.TICK_RATE_HZ
    events = [] # Mock event list
    parent_a.update(mock_game_window.world, dt, current_tick, events)

    # Assertion: Check that a third blob (offspring) has been added
    assert len(mock_game_window.blobs) == 3
    offspring = mock_game_window.blobs[2]
    assert offspring.id == 2
    assert offspring.x == 100
    assert offspring.y == 100

    # Assertion: Check that parents' energy decreased by REPRO_ENERGY_COST, accounting for decay during the update tick
    # Energy decays first, then reproduction cost is subtracted.
    expected_parent_a_energy = int(parent_a_start_energy - parent_a._energy_decay_tick) - config.REPRO_ENERGY_COST
    assert parent_a.energy == expected_parent_a_energy
    # Parent B's energy doesn't decay in this test setup as its update wasn't called directly
    assert parent_b.energy == parent_b_start_energy - config.REPRO_ENERGY_COST

    # Assertion: Check that parents' last_repro_tick is updated to current_tick
    assert parent_a.last_repro_tick == current_tick
    assert parent_b.last_repro_tick == current_tick

    # Assertion: Check offspring's cooldown started
    assert offspring.last_repro_tick == current_tick

    # Assertion: Check log message (uses energy AFTER cost deduction, BEFORE final decay)
    expected_log_energy_a = parent_a_start_energy - config.REPRO_ENERGY_COST
    expected_log_energy_b = parent_b_start_energy - config.REPRO_ENERGY_COST
    assert f"Reproduction: Blob {parent_a.id} (self.energy={expected_log_energy_a}) + Blob {parent_b.id} (mate.energy={expected_log_energy_b}) -> Offspring {offspring.id}" in caplog.text 