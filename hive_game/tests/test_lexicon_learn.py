"""Tests lexicon learning (positive reinforcement and hearing)."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from hive_game.hive.blob import Blob
from hive_game.hive.world import World, ResourceType
from hive_game.hive.game_window import GameWindow
from hive_game.hive import config

# --- Fixtures (similar to test_chirp_emit, could be shared in conftest.py later) ---
@pytest.fixture
def mock_game_window() -> GameWindow:
    window = GameWindow(headless=True)
    window.sound = MagicMock()
    window._chirp_id_iterator = iter(range(256))
    return window

@pytest.fixture
def test_world() -> World:
    return World(width=200, height=200)

# --- Test Cases ---
def test_positive_reinforcement_increases_weight(mock_game_window: GameWindow, test_world: World):
    """Verify Req #4: Hearing chirp + matching outcome reinforces lexicon weight."""
    # Arrange:
    listener = Blob(id=1, x=10, y=10, game_window_ref=mock_game_window)
    emitter = Blob(id=2, x=15, y=15, game_window_ref=mock_game_window) # Nearby
    test_world.tiles[(listener.x, listener.y)] = ResourceType.FOOD
    listener.hunger = config.HUNGER_SEEK + 10 # Make listener hungry
    chirp_id_food = 42 # Arbitrary ID for food chirp
    concept = "food"
    initial_weight = 0.1
    listener.lexicon = {chirp_id_food: {concept: initial_weight}}

    # Simulate hearing the chirp in a previous tick and adding to pending queue
    # Note: _reinforcement_delay_ticks is 180, so expiry is far in future
    expiry_tick = 500
    listener.heard_chirps_pending_reinforcement.append((chirp_id_food, concept, expiry_tick))

    current_tick = 1 # Current tick is well before expiry
    dt = 1.0 / config.TICK_RATE_HZ
    events = [] # Events from *this* frame (should be empty for listener)

    # Act: Listener updates, consumes food. This should trigger positive reinforcement.
    listener.update(test_world, dt, current_tick, events)

    # Assert: Weight for chirp_id_food / food concept should increase
    assert chirp_id_food in listener.lexicon, "Chirp ID lost from lexicon"
    assert concept in listener.lexicon[chirp_id_food], "Concept lost from lexicon entry"
    final_weight = listener.lexicon[chirp_id_food][concept]
    expected_weight = min(1.0, initial_weight + 0.2)
    assert final_weight == pytest.approx(expected_weight, rel=1e-3), "Lexicon weight did not increase correctly"
    assert not listener.heard_chirps_pending_reinforcement, "Pending reinforcement was not removed"

def test_repeated_exposure_strengthens_association(mock_game_window: GameWindow, test_world: World):
    """Verify Req #3 (partially): Multiple exposures reach high weight."""
    # Arrange
    listener = Blob(id=1, x=10, y=10, game_window_ref=mock_game_window)
    chirp_id_food = 55
    concept = "food"
    num_exposures = 10
    current_tick = 0
    dt = 1.0 / config.TICK_RATE_HZ

    # Act: Simulate 10 cycles of hearing chirp -> eating food shortly after
    for i in range(num_exposures):
        current_tick += 1
        # Simulate hearing
        expiry_tick = current_tick + listener._reinforcement_delay_ticks
        listener.heard_chirps_pending_reinforcement.append((chirp_id_food, concept, expiry_tick))

        current_tick += 5 # Simulate a short delay before eating
        # Simulate eating
        test_world.tiles[(listener.x, listener.y)] = ResourceType.FOOD
        listener.hunger = config.HUNGER_SEEK + 10 # Ensure hungry enough
        events = []
        listener.update(test_world, dt, current_tick, events) # This triggers reinforcement

    # Assert: Weight should be close to the target (≥ 0.8 as per spec example 5)
    # Each exposure adds 0.2, capped at 1.0. Decay is negligible over short intervals.
    # 10 * 0.2 = 2.0, so it should reach cap of 1.0
    final_weight = listener.lexicon.get(chirp_id_food, {}).get(concept, 0.0)
    assert final_weight >= 0.8, f"Weight after {num_exposures} exposures too low ({final_weight})"
    assert final_weight == pytest.approx(1.0), "Weight did not reach cap after sufficient exposures"

def test_negative_reinforcement_on_expiry(mock_game_window: GameWindow, test_world: World):
    """Verify negative reinforcement when expectation expires."""
    # Arrange
    listener = Blob(id=1, x=10, y=10, game_window_ref=mock_game_window)
    chirp_id_food = 66
    concept = "food"
    initial_weight = 0.5
    listener.lexicon = {chirp_id_food: {concept: initial_weight}}

    # Simulate hearing a chirp long ago, expiry is now
    start_tick = 10
    expiry_tick = start_tick + listener._reinforcement_delay_ticks # Exactly 180 ticks later
    listener.heard_chirps_pending_reinforcement.append((chirp_id_food, concept, expiry_tick))

    current_tick = expiry_tick # The exact tick when it should expire
    dt = 1.0 / config.TICK_RATE_HZ
    events = [] # No relevant events this frame

    # Act: Update the listener. Should process the queue and apply negative reinforcement.
    listener.update(test_world, dt, current_tick, events)

    # Assert: Weight should decrease, item removed from queue
    assert chirp_id_food in listener.lexicon, "Chirp ID lost from lexicon"
    assert concept in listener.lexicon[chirp_id_food], "Concept lost from lexicon entry"
    final_weight = listener.lexicon[chirp_id_food][concept]
    expected_weight = max(0.0, initial_weight - 0.05)
    assert final_weight == pytest.approx(expected_weight, rel=1e-3), "Negative reinforcement applied incorrectly"
    assert not listener.heard_chirps_pending_reinforcement, "Expired reinforcement was not removed"

def test_hearing_adds_to_pending_queue(mock_game_window: GameWindow):
    """Verify hearing a nearby chirp adds entry to reinforcement queue."""
     # Arrange:
    listener = Blob(id=1, x=10, y=10, game_window_ref=mock_game_window)
    emitter_id = 2
    chirp_id = 77
    emitter_x, emitter_y = 15, 15 # Within CHIRP_RADIUS (32)
    listener.hunger = config.HUNGER_SEEK + 10 # Make listener hungry -> expect food
    current_tick = 100
    dt = 1.0 / config.TICK_RATE_HZ
    # Simulate a chirp event from the emitter
    events = [("chirp", emitter_id, chirp_id, emitter_x, emitter_y)]

    # Act: Update the listener. _process_heard_chirps should run.
    test_world = mock_game_window.world
    listener.update(test_world, dt, current_tick, events)

    # Assert: An item should be in the pending queue
    assert len(listener.heard_chirps_pending_reinforcement) == 1, "No item added to pending queue"
    pending_item = listener.heard_chirps_pending_reinforcement[0]
    assert pending_item[0] == chirp_id, "Incorrect chirp ID in queue"
    assert pending_item[1] == "food", "Incorrect concept guess in queue"
    assert pending_item[2] == current_tick + listener._reinforcement_delay_ticks, "Incorrect expiry tick in queue" 