"""Tests reproduction and mutation logic (Phase 2.5)."""
from __future__ import annotations

import pytest
import random
import logging
from unittest.mock import MagicMock

from hive_game.hive.blob import Blob
from hive_game.hive.world import World
from hive_game.hive.game_window import GameWindow
from hive_game.hive import config

log = logging.getLogger(__name__)

# --- Fixtures ---
@pytest.fixture
def mock_game_window() -> GameWindow:
    window = GameWindow(headless=True)
    window.sound = MagicMock() # Mock sound to avoid errors
    # Reset blob list for tests that modify population
    window.blobs = []
    window.next_blob_id = 0
    return window

@pytest.fixture
def eligible_blob(mock_game_window: GameWindow) -> Blob:
    """Creates a blob meeting basic reproduction criteria."""
    blob = Blob(
        id=mock_game_window.get_next_blob_id(),
        x=10, y=10,
        game_window_ref=mock_game_window,
        hunger=config.REPRO_HUNGER_THRESH - 1,
        thirst=config.REPRO_THIRST_THRESH - 1,
        energy=config.REPRO_ENERGY_THRESH + 1,
        last_repro_tick = -10000 # Ensure cooldown is not active
    )
    mock_game_window.blobs.append(blob) # Add to window's list
    return blob

@pytest.fixture
def eligible_mate(mock_game_window: GameWindow) -> Blob:
    """Creates a second eligible blob nearby."""
    mate = Blob(
        id=mock_game_window.get_next_blob_id(),
        x=15, y=15, # Within REPRO_NEARBY_RADIUS
        game_window_ref=mock_game_window,
        hunger=config.REPRO_HUNGER_THRESH - 5,
        thirst=config.REPRO_THIRST_THRESH - 5,
        energy=config.REPRO_ENERGY_THRESH + 5,
        last_repro_tick = -10000
    )
    mock_game_window.blobs.append(mate)
    return mate

# --- Test Cases ---
def test_reproduce_energy_cost(eligible_blob: Blob, eligible_mate: Blob):
    """Verify parents' energy drops by REPRO_ENERGY_COST."""
    # Arrange
    initial_energy_parent1 = eligible_blob.energy
    initial_energy_parent2 = eligible_mate.energy
    current_tick = 100

    # Act
    # Simulate parent1 initiating reproduction
    eligible_blob.reproduce_with(eligible_mate, current_tick)

    # Assert
    assert eligible_blob.energy == initial_energy_parent1 - config.REPRO_ENERGY_COST
    assert eligible_mate.energy == initial_energy_parent2 - config.REPRO_ENERGY_COST

def test_reproduction_resets_cooldown(eligible_blob: Blob, eligible_mate: Blob):
    """Verify reproduction sets last_repro_tick for both parents."""
    # Arrange
    assert eligible_blob.last_repro_tick < 0
    assert eligible_mate.last_repro_tick < 0
    current_tick = 200

    # Act
    eligible_blob.reproduce_with(eligible_mate, current_tick)

    # Assert
    assert eligible_blob.last_repro_tick == current_tick
    assert eligible_mate.last_repro_tick == current_tick

def test_offspring_mutation(eligible_blob: Blob, eligible_mate: Blob, mock_game_window: GameWindow):
    """Verify offspring wander_propensity is mutated within +/- 5% of parent average."""
    # Arrange
    eligible_blob.wander_propensity = 0.10
    eligible_mate.wander_propensity = 0.20
    parent_average = (0.10 + 0.20) / 2.0 # = 0.15
    lower_bound = parent_average * 0.95
    upper_bound = parent_average * 1.05
    current_tick = 300

    # Act
    # Ensure random gives different results over multiple tries
    random.seed() # Use system time for less predictable mutation
    offspring_props = []
    initial_pop_size = len(mock_game_window.blobs)
    for _ in range(20): # Create multiple offspring
        eligible_blob.reproduce_with(eligible_mate, current_tick)
        # Reset parent energy/cooldown for next loop iteration if needed, or just check last offspring
        eligible_blob.energy += config.REPRO_ENERGY_COST
        eligible_mate.energy += config.REPRO_ENERGY_COST
        eligible_blob.last_repro_tick = -10000
        eligible_mate.last_repro_tick = -10000
        current_tick += 1
    
    offspring_list = mock_game_window.blobs[initial_pop_size:]
    assert len(offspring_list) == 20, "Did not generate enough offspring"

    # Assert
    mutated = False
    for offspring in offspring_list:
        prop = offspring.wander_propensity
        assert lower_bound <= prop <= upper_bound, f"Offspring wander_propensity {prop} out of bounds [{lower_bound:.3f}, {upper_bound:.3f}]"
        if not (prop == pytest.approx(parent_average)): # Check if mutation actually happened
             mutated = True
             
    assert mutated, "Offspring wander_propensity was never different from the parent average over 20 trials"

def test_population_cap(eligible_blob: Blob, eligible_mate: Blob, mock_game_window: GameWindow):
    """Verify reproduction stops when MAX_BLOBS is reached."""
    # Arrange
    config.MAX_BLOBS = 3 # Set a low cap for testing (2 parents + 1 offspring max)
    assert len(mock_game_window.blobs) == 2 # Starts with parent + mate
    current_tick = 400

    # Act: First reproduction should succeed
    eligible_blob.reproduce_with(eligible_mate, current_tick)
    assert len(mock_game_window.blobs) == 3

    # Reset cooldowns/energy to allow another attempt
    eligible_blob.last_repro_tick = -10000
    eligible_mate.last_repro_tick = -10000
    eligible_blob.energy += config.REPRO_ENERGY_COST
    eligible_mate.energy += config.REPRO_ENERGY_COST
    current_tick += 10

    # Act: Attempt second reproduction - should be blocked by can_reproduce check
    can_repro_again = eligible_blob.can_reproduce(current_tick)
    # Explicitly call find_mate and reproduce_with to ensure add_blob handles cap if can_reproduce fails
    mate_again = eligible_blob.find_mate() 
    if can_repro_again and mate_again and mate_again.can_reproduce(current_tick):
         eligible_blob.reproduce_with(mate_again, current_tick)

    # Assert: Population should not exceed the cap
    assert not can_repro_again, "Blob should not be able to reproduce when MAX_BLOBS reached"
    assert len(mock_game_window.blobs) == 3, "Population exceeded MAX_BLOBS"
    # Restore original cap if needed for other tests, though fixtures should isolate this
    config.MAX_BLOBS = 1000

def test_reproduction_cooldown(eligible_blob: Blob, eligible_mate: Blob, mock_game_window: GameWindow):
    """Verify cooldown prevents immediate re-reproduction."""
    # Arrange
    current_tick = 500
    initial_energy = eligible_blob.energy # Store initial energy if needed elsewhere
    eligible_blob.reproduce_with(eligible_mate, current_tick)
    assert eligible_blob.last_repro_tick == current_tick  # Verify setup
    assert len(mock_game_window.blobs) == 3 # 2 parents, 1 offspring
    
    # Restore energy after initial reproduction for subsequent checks
    eligible_blob.energy += config.REPRO_ENERGY_COST

    # Act: Attempt reproduction immediately after (next tick)
    can_repro_now = eligible_blob.can_reproduce(current_tick + 1)
    log.debug(f"Immediate reproduction check: {can_repro_now}")
    # Assert
    assert not can_repro_now, "Blob should not be able to reproduce due to cooldown"

    # Act: Attempt reproduction just before cooldown expires
    cooldown_ticks_int = int(config.REPRO_COOLDOWN_S * config.TICK_RATE_HZ)
    test_tick_before = current_tick + cooldown_ticks_int - 1
    log.debug(f"Testing reproduction before cooldown: current_tick={current_tick}, cooldown_ticks_int={cooldown_ticks_int}, test_tick={test_tick_before}")
    can_repro_before = eligible_blob.can_reproduce(test_tick_before)
    log.debug(f"Pre-cooldown reproduction check: {can_repro_before}")
    assert not can_repro_before, "Blob should not be able to reproduce just before cooldown expires"

    # Act: Attempt reproduction exactly when cooldown expires
    test_tick_after = current_tick + cooldown_ticks_int
    log.debug(f"Testing reproduction at cooldown: current_tick={current_tick}, cooldown_ticks_int={cooldown_ticks_int}, test_tick={test_tick_after}")

    # Add logging to check state right before the call
    log.debug(f"Blob state before final check: ID={eligible_blob.id}, Hunger={eligible_blob.hunger}, Thirst={eligible_blob.thirst}, Energy={eligible_blob.energy}, Alive={eligible_blob.alive}, LastRepro={eligible_blob.last_repro_tick}")

    can_repro_after = eligible_blob.can_reproduce(test_tick_after)
    log.debug(f"At-cooldown reproduction check: {can_repro_after}")
    assert can_repro_after, "Blob should be able to reproduce exactly when cooldown expires"