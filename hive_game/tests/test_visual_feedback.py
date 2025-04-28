"""Tests visual feedback features like action bubbles and debug panel."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
import arcade

from hive_game.hive.game_window import GameWindow
from hive_game.hive.blob import Blob
from hive_game.hive import config

# --- Fixtures ---
@pytest.fixture
def mock_window() -> GameWindow:
    """Provides a GameWindow instance suitable for draw testing."""
    # Patch arcade drawing functions that cause errors in test context
    # We don't need to test actual resource/blob drawing here.
    with patch("arcade.draw.draw_lbwh_rectangle_filled", MagicMock()), \
         patch("hive_game.hive.blob.Blob.draw", MagicMock()), \
         patch("arcade.Window.clear", MagicMock()): # Also patch clear
        
        # Initialize headless first to avoid HUD errors
        window = GameWindow(headless=True)
        # Set headless to False so on_draw logic runs past the initial check
        window._headless = False
        
        # Mock the specific drawing methods we *are* testing
        window._draw_bubble = MagicMock(name="_draw_bubble")
        window._draw_debug_panel = MagicMock(name="_draw_debug_panel")
        window.blobs = [] # Start with no blobs
        yield window

@pytest.fixture
def sample_blob(mock_window: GameWindow) -> Blob:
    """Provides a single sample blob added to the window."""
    blob = Blob(id=0, x=100, y=100, game_window_ref=mock_window)
    mock_window.blobs.append(blob)
    return blob

# --- Test Cases ---

def test_debug_toggle(mock_window: GameWindow):
    """Verify pressing F2 toggles the debug_mode flag."""
    initial_state = config.SHOW_DEBUG_DEFAULT
    assert mock_window.debug_mode == initial_state, "Initial state doesn't match config"

    # Press F2 once
    mock_window.on_key_press(arcade.key.F2, None)
    assert mock_window.debug_mode == (not initial_state), "Debug mode did not toggle on first press"

    # Press F2 again
    mock_window.on_key_press(arcade.key.F2, None)
    assert mock_window.debug_mode == initial_state, "Debug mode did not toggle back on second press"

def test_bubble_visibility_window(mock_window: GameWindow, sample_blob: Blob):
    """Test that the bubble is drawn only within its duration."""
    # Arrange
    sample_blob.last_emit_concept = "food" # Need a concept to trigger drawing
    bubble_duration = config.BUBBLE_DURATION_TICKS

    # Act & Assert: Bubble visible immediately after emit (Tick 0 vs Tick 0)
    mock_window.current_tick = 0
    sample_blob.last_emit_tick = 0
    mock_window.on_draw()
    mock_window._draw_bubble.assert_called_with(sample_blob)
    mock_window._draw_bubble.reset_mock()

    # Act & Assert: Bubble visible at the end of duration (Tick 60 vs Tick 0)
    mock_window.current_tick = bubble_duration
    sample_blob.last_emit_tick = 0 # Emitted at tick 0
    mock_window.on_draw()
    mock_window._draw_bubble.assert_called_with(sample_blob)
    mock_window._draw_bubble.reset_mock()

    # Act & Assert: Bubble NOT visible just after duration (Tick 61 vs Tick 0)
    mock_window.current_tick = bubble_duration + 1
    sample_blob.last_emit_tick = 0 # Emitted at tick 0
    mock_window.on_draw()
    mock_window._draw_bubble.assert_not_called()
    mock_window._draw_bubble.reset_mock()

    # Act & Assert: Bubble NOT visible if concept is None
    sample_blob.last_emit_concept = None
    mock_window.current_tick = 0
    sample_blob.last_emit_tick = 0
    mock_window.on_draw()
    mock_window._draw_bubble.assert_not_called()

def test_debug_panel_draws_when_active_and_hovered(mock_window: GameWindow, sample_blob: Blob):
    """Verify debug panel draws only when debug mode is on and a blob is hovered."""
    # Arrange: Debug on, blob hovered
    mock_window.debug_mode = True
    mock_window._hovered_blob = sample_blob

    # Act
    mock_window.on_draw()

    # Assert
    mock_window._draw_debug_panel.assert_called_once_with(sample_blob)

def test_debug_panel_not_drawn_when_inactive(mock_window: GameWindow, sample_blob: Blob):
    """Verify debug panel doesn't draw when debug mode is off."""
    # Arrange: Debug off, blob hovered
    mock_window.debug_mode = False
    mock_window._hovered_blob = sample_blob

    # Act
    mock_window.on_draw()

    # Assert
    mock_window._draw_debug_panel.assert_not_called()

def test_debug_panel_not_drawn_when_not_hovered(mock_window: GameWindow, sample_blob: Blob):
    """Verify debug panel doesn't draw when no blob is hovered."""
    # Arrange: Debug on, nothing hovered
    mock_window.debug_mode = True
    mock_window._hovered_blob = None

    # Act
    mock_window.on_draw()

    # Assert
    mock_window._draw_debug_panel.assert_not_called() 