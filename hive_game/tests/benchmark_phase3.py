"""Benchmarks Phase 3 performance (chirps + lexicon)."""
from __future__ import annotations

import pytest
from unittest.mock import patch

# Ensure pytest-benchmark is installed: pip install pytest-benchmark

from hive_game.hive.game_window import GameWindow
from hive_game.hive import config

# Use a larger blob count for benchmarking
BENCHMARK_BLOB_COUNT = 1000

@pytest.fixture(scope="module")
def game_window_phase3() -> GameWindow:
    """Fixture to set up the game window with Phase 3 features for benchmark."""
    # Override blob count for benchmark
    original_blob_count = config.BLOB_COUNT
    config.BLOB_COUNT = BENCHMARK_BLOB_COUNT
    
    # Use headless mode for benchmark
    # Mock sound playing as it involves I/O we don't want to measure here.
    with patch('hive_game.hive.sound.play_chirp') as _: 
        window = GameWindow(headless=True)
    
    # Restore original config value after window creation
    config.BLOB_COUNT = original_blob_count
    return window

@pytest.mark.benchmark(group="phase3_update")
def test_phase3_update_performance(benchmark, game_window_phase3: GameWindow):
    """Benchmarks the core on_update logic with Phase 3 features.
    
    Verifies Requirement #7 (Performance hit ≤ 0.5 ms for 1000 blobs vs Phase 2 baseline).
    Note: This requires a baseline benchmark from Phase 2 to compare against.
    We will aim for the update time itself to be low (e.g., under 1-2ms total for 1k blobs).
    The exact comparison against P2 baseline needs external tracking.
    """
    # The benchmark fixture runs the function multiple times
    
    # Use the internal _update_only method which skips rendering/HUD updates
    # Pass a typical delta_time
    dt = 1.0 / config.TICK_RATE_HZ
    benchmark(game_window_phase3._update_only, dt)

# Optional: Add baseline benchmark from Phase 2 if code exists
# @pytest.mark.benchmark(group="phase2_update")
# def test_phase2_update_performance(benchmark, game_window_phase2: GameWindow):
#     """ Baseline benchmark using Phase 2 code setup (if available) """
#     dt = 1.0 / config.TICK_RATE_HZ
#     benchmark(game_window_phase2._update_only, dt) 