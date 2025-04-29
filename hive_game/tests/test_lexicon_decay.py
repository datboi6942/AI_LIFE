"""Tests lexicon weight decay."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock
import math

from hive_game.hive.blob import Blob
from hive_game.hive.world import World
from hive_game.hive.game_window import GameWindow
from hive_game.hive import config
from hive_game.hive.resource_type import ResourceType

# --- Fixtures ---
@pytest.fixture
def mock_game_window() -> GameWindow:
    window = GameWindow(headless=True)
    window.sound = MagicMock()
    window._chirp_id_iterator = iter(range(256))
    return window

@pytest.fixture
def test_world() -> World:
    return World(width=100, height=100)

@pytest.fixture
def test_blob(mock_game_window: GameWindow) -> Blob:
    blob = Blob(id=1, x=10, y=10, game_window_ref=mock_game_window, energy=1_000_000)
    # Initialize lexicon with some weights
    blob.lexicon = {
        10: {"food": 0.8, "water": 0.1},
        20: {"water": 0.9}
    }
    return blob

# --- Test Cases ---
def test_lexicon_decay_over_time(test_blob: Blob, test_world: World):
    """Verify Req #5: Lexicon weights decay over time without reinforcement."""
    # Arrange
    initial_weight_food = test_blob.lexicon[10]["food"]
    initial_weight_water = test_blob.lexicon[20]["water"]
    
    simulation_time_s = 50.0 # Simulate 50 seconds
    num_ticks = int(simulation_time_s * config.TICK_RATE_HZ)
    dt = 1.0 / config.TICK_RATE_HZ
    events = []

    # Act: Run blob update for the specified duration without any reinforcement events
    for tick in range(num_ticks):
        test_blob.update(test_world, dt, tick, events)
        # Ensure no accidental reinforcement happens
        assert not test_blob.heard_chirps_pending_reinforcement
        assert test_world.get_tile(test_blob.x, test_blob.y) == ResourceType.EMPTY

    # Assert: Weights should have decayed according to the formula
    # Final Weight = Initial Weight * (1 - LEXICON_DECAY * dt)^num_ticks
    # Or Final Weight = Initial Weight * (1 - LEXICON_DECAY)^(simulation_time_s) approx.
    decay_factor_tick = (1.0 - config.LEXICON_DECAY * dt)
    expected_decay_multiplier = decay_factor_tick ** num_ticks
    
    final_weight_food = test_blob.lexicon.get(10, {}).get("food", 0.0)
    final_weight_water = test_blob.lexicon.get(20, {}).get("water", 0.0)
    
    expected_final_food = initial_weight_food * expected_decay_multiplier
    expected_final_water = initial_weight_water * expected_decay_multiplier

    assert final_weight_food == pytest.approx(expected_final_food, abs=1e-3), \
        f"Food weight decay incorrect. Expected ~{expected_final_food:.3f}, Got {final_weight_food:.3f}"
    assert final_weight_water == pytest.approx(expected_final_water, abs=1e-3), \
        f"Water weight decay incorrect. Expected ~{expected_final_water:.3f}, Got {final_weight_water:.3f}"

    # Spec example: Weight halves after 50s idle (LEXICON_DECAY=0.01 => e^(-0.01*50) = e^-0.5 ≈ 0.606)
    # Let's check if the 50s decay matches roughly 0.6 multiplier
    assert expected_decay_multiplier == pytest.approx(math.exp(-config.LEXICON_DECAY * simulation_time_s), rel=0.1), \
        f"Decay multiplier {expected_decay_multiplier:.3f} doesn't match exp target {math.exp(-config.LEXICON_DECAY * simulation_time_s):.3f}"
    
    # Check the spec's specific example target (halving -> 0.5 vs ~0.6 calc)
    # The spec says "Weight halves after 50 s idle (~0.6)" - this seems slightly contradictory.
    # Let's test against the calculated ~0.6 multiplier derived from the decay formula.
    assert final_weight_food / initial_weight_food == pytest.approx(expected_decay_multiplier, rel=0.05)

def test_decay_removes_near_zero_weights(test_blob: Blob, test_world: World):
    """Verify that decay eventually removes very small weights."""
    # Arrange: Add a very small weight
    test_blob.lexicon[30] = {"food": 0.0001}
    num_ticks = int(5 * config.TICK_RATE_HZ) # 5 seconds should be enough to kill it
    dt = 1.0 / config.TICK_RATE_HZ
    events = []

    # Act
    for tick in range(num_ticks):
        test_blob.update(test_world, dt, tick, events)

    # Assert: The entry for chirp 30 / food should be gone
    assert 30 not in test_blob.lexicon or "food" not in test_blob.lexicon[30], \
        "Near-zero weight was not removed by decay cleanup" 