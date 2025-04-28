"""Tests the Jaccard similarity calculation for convergence."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from hive_game.hive import hive_mind
from hive_game.hive.blob import Blob
from hive_game.hive.game_window import GameWindow

# --- Fixtures ---
@pytest.fixture
def mock_game_window() -> GameWindow:
    # Needs blobs list, but doesn't need graphics or full setup
    window = GameWindow(headless=True)
    window.sound = MagicMock()
    window._chirp_id_iterator = iter(range(256))
    # Need blobs for update_convergence
    window.blobs = []
    return window

# Helper to create a blob with a specific lexicon
def create_blob_with_lexicon(id: int, lexicon: dict, gw: GameWindow) -> Blob:
    blob = Blob(id=id, x=0, y=0, game_window_ref=gw)
    blob.lexicon = lexicon
    return blob

# --- Test Cases for calculate_jaccard_similarity ---

@pytest.mark.parametrize(
    "set1, set2, expected",
    [
        ({1, 2, 3}, {1, 2, 3}, 1.0), # Identical sets
        ({1, 2, 3}, {4, 5, 6}, 0.0), # Disjoint sets
        ({1, 2, 3}, {1, 2, 4}, 2/4), # Partial overlap (1, 2)
        ({1, 2}, {1, 2, 3, 4}, 2/4), # Subset
        (set(), set(), 1.0),          # Both empty
        ({1, 2, 3}, set(), 0.0),      # One empty
        (set(), {1, 2, 3}, 0.0),      # Other empty
    ]
)
def test_calculate_jaccard_similarity(set1, set2, expected):
    """Tests the core Jaccard calculation utility."""
    assert hive_mind.calculate_jaccard_similarity(set1, set2) == pytest.approx(expected)

# --- Test Cases for update_convergence --- 

def test_update_convergence_identical_lexicons(mock_game_window: GameWindow):
    """Verify convergence is 1.0 for identical lexicons."""
    lexicon = {10: {"food": 0.8}, 20: {"water": 0.7}}
    blobs = [
        create_blob_with_lexicon(1, lexicon, mock_game_window),
        create_blob_with_lexicon(2, lexicon, mock_game_window),
        create_blob_with_lexicon(3, lexicon, mock_game_window)
    ]
    mock_game_window.blobs = blobs
    # Trigger calculation at the exact interval
    result = hive_mind.update_convergence(blobs, 5000, 5000, dominant_threshold=0.6)
    assert result == pytest.approx(1.0)

def test_update_convergence_disjoint_lexicons(mock_game_window: GameWindow):
    """Verify convergence is 0.0 for completely different dominant chirps."""
    lexicon1 = {10: {"food": 0.8}, 20: {"water": 0.7}} # Dominant: {10}, {20}
    lexicon2 = {11: {"food": 0.9}, 21: {"water": 0.6}} # Dominant: {11}, {21}
    blobs = [
        create_blob_with_lexicon(1, lexicon1, mock_game_window),
        create_blob_with_lexicon(2, lexicon2, mock_game_window)
    ]
    mock_game_window.blobs = blobs
    result = hive_mind.update_convergence(blobs, 5000, 5000, dominant_threshold=0.6)
    assert result == pytest.approx(0.0)

def test_update_convergence_partial_overlap(mock_game_window: GameWindow):
    """Verify convergence calculation for partial lexicon overlap."""
    # Blob 1: Food={10}, Water={20}
    lex1 = {10: {"food": 0.8}, 20: {"water": 0.7}}
    # Blob 2: Food={10}, Water={21}
    lex2 = {10: {"food": 0.9}, 21: {"water": 0.6}}
    # Blob 3: Food={11}, Water={20}
    lex3 = {11: {"food": 0.7}, 20: {"water": 0.8}}
    blobs = [
        create_blob_with_lexicon(1, lex1, mock_game_window),
        create_blob_with_lexicon(2, lex2, mock_game_window),
        create_blob_with_lexicon(3, lex3, mock_game_window)
    ]
    mock_game_window.blobs = blobs
    
    # Pairs:
    # (1, 2): Food J=1/1=1.0, Water J=0/2=0.0 -> Avg = 0.5
    # (1, 3): Food J=0/2=0.0, Water J=1/1=1.0 -> Avg = 0.5
    # (2, 3): Food J=0/2=0.0, Water J=0/2=0.0 -> Avg = 0.0
    # Total Avg = (0.5 + 0.5 + 0.0) / 3 = 1.0 / 3 = 0.333...
    expected_result = 1.0 / 3.0

    result = hive_mind.update_convergence(blobs, 5000, 5000, dominant_threshold=0.6)
    assert result == pytest.approx(expected_result)

def test_update_convergence_ignores_below_threshold(mock_game_window: GameWindow):
    """Verify weights below threshold don't count towards dominant sets."""
    lex1 = {10: {"food": 0.8}, 20: {"water": 0.5}} # Dominant: Food={10}, Water={}
    lex2 = {10: {"food": 0.9}, 20: {"water": 0.4}} # Dominant: Food={10}, Water={}
    blobs = [
        create_blob_with_lexicon(1, lex1, mock_game_window),
        create_blob_with_lexicon(2, lex2, mock_game_window)
    ]
    mock_game_window.blobs = blobs
    # Food J=1/1=1.0, Water J=0/0=1.0 -> Avg = 1.0
    result = hive_mind.update_convergence(blobs, 5000, 5000, dominant_threshold=0.6)
    assert result == pytest.approx(1.0)

def test_update_convergence_only_at_interval(mock_game_window: GameWindow):
    """Verify calculation only happens on interval ticks."""
    lexicon = {10: {"food": 0.8}}
    blobs = [create_blob_with_lexicon(1, lexicon, mock_game_window)]
    mock_game_window.blobs = blobs

    interval = 5000
    # Should not run
    assert hive_mind.update_convergence(blobs, interval - 1, interval) is None
    assert hive_mind.update_convergence(blobs, interval + 1, interval) is None
    assert hive_mind.update_convergence(blobs, 1, interval) is None
    # Should run
    assert hive_mind.update_convergence(blobs, interval, interval) is not None
    assert hive_mind.update_convergence(blobs, interval * 2, interval) is not None
    assert hive_mind.update_convergence(blobs, 0, interval) is not None # Runs at tick 0

def test_update_convergence_handles_no_blobs(mock_game_window: GameWindow):
    """Verify returns None if no blobs provided."""
    mock_game_window.blobs = []
    assert hive_mind.update_convergence([], 5000, 5000) is None

def test_update_convergence_handles_one_blob(mock_game_window: GameWindow):
    """Verify returns 1.0 if only one blob exists (no pairs to compare)."""
    lexicon = {10: {"food": 0.8}}
    blobs = [create_blob_with_lexicon(1, lexicon, mock_game_window)]
    mock_game_window.blobs = blobs
    assert hive_mind.update_convergence(blobs, 5000, 5000) == pytest.approx(1.0) 