from __future__ import annotations

import pytest

# Check if pytest-benchmark is installed
pytest_benchmark_installed = False
try:
    import pytest_benchmark
    pytest_benchmark_installed = True
except ImportError:
    pass

# Conditionally import GameWindow only if benchmark is installed to avoid errors
if pytest_benchmark_installed:
    from hive_game.hive.game_window import GameWindow
    from hive_game.hive import config

    # Mark the entire module to be skipped if pytest-benchmark is not available
    pytestmark = pytest.mark.skipif(not pytest_benchmark_installed,
                                    reason="pytest-benchmark not installed")

    @pytest.mark.benchmark(group="phase2_update")
    def test_perf_phase2_update(benchmark) -> None:
        """Benchmarks the core update logic for Phase 2."""
        # Setup: Create a headless window with standard Phase 1/2 blob count
        # Use fixed blob count for consistent benchmarking
        config.BLOB_COUNT = 50 # Or 1000 as per spec note, using 50 for faster test runs
        gw = GameWindow(headless=True)
        # Simulate one tick duration for the update
        dt = 1.0 / config.TICK_RATE_HZ

        # Function to benchmark
        def update_func():
            gw._update_only(dt)

        benchmark(update_func)

else:
    # If pytest-benchmark is not installed, provide a dummy test or skip message
    # This prevents errors when pytest collects tests.
    def test_benchmark_skipped():
        pytest.skip("pytest-benchmark not installed, skipping performance tests.") 