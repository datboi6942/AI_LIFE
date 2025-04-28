"""Tests chirp emission logic."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from hive_game.hive.blob import Blob
from hive_game.hive.world import World, ResourceType
from hive_game.hive.game_window import GameWindow
from hive_game.hive import config

# Minimal setup for testing Blob updates without full GameWindow graphics
@pytest.fixture
def mock_game_window() -> GameWindow:
    """Creates a minimal mock GameWindow suitable for Blob testing."""
    # Use headless mode to avoid needing graphics context
    window = GameWindow(headless=True)
    # Mock sound playing to avoid audio errors during test
    window.sound = MagicMock()
    # Provide a way to get a new chirp ID deterministically for tests
    window._chirp_id_iterator = iter(range(10)) # Provide a few IDs
    return window

@pytest.fixture
def test_blob(mock_game_window: GameWindow) -> Blob:
    """Creates a single Blob instance for testing."""
    return Blob(id=1, x=10, y=10, game_window_ref=mock_game_window)

@pytest.fixture
def test_world() -> World:
    """Creates a World instance for testing."""
    return World(width=100, height=100)


@patch('hive_game.hive.sound.play_chirp') # Mock sound playback
def test_chirp_on_food_discovery(mock_play_chirp: MagicMock, test_blob: Blob, test_world: World, mock_game_window: GameWindow):
    """Verify Requirement 1 & 2: Blob emits chirp event on eating food."""
    # Arrange: Place food, make blob hungry, ensure no cooldown
    food_x, food_y = test_blob.x, test_blob.y
    test_world.tiles[(food_x, food_y)] = ResourceType.FOOD
    test_blob.hunger = config.BLOB_MAX_NEEDS - 1 # Very hungry
    test_blob.last_chirp_time = -100.0 # Ensure cooldown isn't active
    events = []
    current_tick = 1
    dt = 1.0 / config.TICK_RATE_HZ

    # Act: Update the blob once (should consume food and chirp)
    test_blob.update(test_world, dt, current_tick, events)

    # Assert: Check if a chirp event was added to the queue
    assert len(events) > 0, "No events were generated"
    found_chirp = False
    emitted_chirp_id = -1
    for event in events:
        if event[0] == "chirp":
            assert event[1] == test_blob.id, "Chirp emitter ID mismatch"
            assert event[3] == test_blob.x, "Chirp location X mismatch"
            assert event[4] == test_blob.y, "Chirp location Y mismatch"
            emitted_chirp_id = event[2] # Store the ID
            found_chirp = True
            break
    assert found_chirp, "Chirp event was not found in the event queue"

    # Assert: Check if the correct chirp ID was associated in the lexicon (initial allocation)
    assert emitted_chirp_id in test_blob.lexicon, "Emitted chirp ID not in lexicon"
    assert "food" in test_blob.lexicon[emitted_chirp_id], "'food' concept not in lexicon for chirp ID"
    assert test_blob.lexicon[emitted_chirp_id]["food"] == 0.2, "Initial lexicon weight incorrect"

    # Assert: Check that play_sound was called with the correct ID
    mock_play_chirp.assert_called_once_with(emitted_chirp_id, mock_game_window)

@patch('hive_game.hive.sound.play_chirp')
def test_no_chirp_if_cooldown_active(mock_play_chirp: MagicMock, test_blob: Blob, test_world: World, mock_game_window: GameWindow):
    """Verify blob respects chirp cooldown."""
    # Arrange: Place food, make blob hungry, set recent chirp time
    food_x, food_y = test_blob.x, test_blob.y
    test_world.tiles[(food_x, food_y)] = ResourceType.FOOD
    test_blob.hunger = config.BLOB_MAX_NEEDS - 1
    current_tick = 180 # Arbitrary tick
    dt = 1.0 / config.TICK_RATE_HZ
    test_blob.last_chirp_time = (current_tick - 10) / config.TICK_RATE_HZ # Just chirped 10 ticks ago
    events = []

    # Act: Update the blob (should consume food but NOT chirp)
    test_blob.update(test_world, dt, current_tick, events)

    # Assert: No chirp event should be in the queue, sound not played
    assert not any(event[0] == "chirp" for event in events), "Chirp event generated despite cooldown"
    mock_play_chirp.assert_not_called() 