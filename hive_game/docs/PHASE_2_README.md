# Phase 2: Memory-Driven Seeking - Design Rationale & Performance

**Version:** v0.2.0

## Goals

Building on Phase 1, enable Blobs to remember the last known locations of Food and Water tiles. When needs exceed configured thresholds (`HUNGER_SEEK`, `THIRST_SEEK`), Blobs should actively move towards the remembered location instead of wandering randomly.

- **Memory:** Each Blob stores `last_food_pos` and `last_water_pos` (coordinates).
- **Seeking Trigger:** Activated when `hunger >= HUNGER_SEEK` or `thirst >= THIRST_SEEK`.
- **Prioritization:** If both needs are high, the Blob seeks the resource corresponding to the higher need (hunger breaks ties).
- **Memory Decay:** Memories expire after `MEMORY_SPAN_S` seconds.
- **Memory Invalidation:** Memories are cleared if the resource at the remembered location is consumed by another blob or disappears.
- **Fallback:** If no relevant memory exists or needs are below thresholds, the Blob reverts to random wandering.

## Key Implementation Details

- **Configuration:** Added `HUNGER_SEEK`, `THIRST_SEEK`, `MEMORY_SPAN_S`, `SEEK_SPEED` to `hive/config.py`.
- **Blob State:** Added `last_food_pos`, `last_water_pos`, `food_mem_age`, `water_mem_age` fields to the `Blob` dataclass.
- **Memory Update:** When a Blob consumes food/water, its corresponding `last_..._pos` is updated to its current location, and the `..._mem_age` is reset to 0.0.
- **Decay Logic:** A new `_decay_mem(dt, world)` method increments memory ages and checks for expiry (age > `MEMORY_SPAN_S`) or resource absence (`world.tile_is_empty()`). Invalid memories are set to `None`.
- **Target Decision:** `_decide_target()` method checks needs against thresholds and memory validity, returning the target coordinates or `None`.
- **Movement:** The `_move(world)` method (replacing `_wander`) first calls `_decide_target()`. If a target exists, it calculates a simple axis-aligned step (`dx`, `dy`) towards the target using `SEEK_SPEED`. Otherwise, it generates random `dx`, `dy` for wandering. Movement is clamped to world bounds and aligned to the grid.
- **World Helpers:** Added `tile_is_food()`, `tile_is_water()`, `tile_is_empty()` to `World` for clearer checks in memory decay.
- **Benchmarking Support:** `GameWindow` updated with a `headless` mode and `_update_only` method to facilitate performance testing without graphics overhead.

## Performance Notes

- **Target:** Seeking logic adds `≤ 0.4 ms` for 1000 blobs compared to Phase 1 baseline `on_update` time.
- **Seeking Algorithm:** Uses simple axis-aligned steps (no complex pathfinding or math), keeping computation minimal.
- **Memory Overhead:** Adds 2 `Optional[tuple]` and 2 `float` per blob (~32 bytes extra per blob worst-case), negligible impact expected.
- **World Checks:** `tile_is_empty/food/water` rely on the O(1) dictionary lookup in `World.get_tile`.
- **Overall:** The additional logic per blob (`_decay_mem`, `_decide_target`) is computationally cheap. The primary performance characteristic remains dominated by iterating through blobs and Python overhead, similar to Phase 1. 