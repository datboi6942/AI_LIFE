# Phase 2: Memory and Seeking

This phase introduces basic memory and purposeful movement (seeking) to the blobs.

## Behavioural Rules

1.  **Memory:** Blobs remember the location of the last food or water tile they consumed.
2.  **Memory Decay:** Memories expire after `MEMORY_SPAN_S` seconds.
3.  **Memory Invalidation:** Memories are forgotten immediately if the resource at the remembered location is consumed by another blob or otherwise removed.
4.  **Seeking Trigger:** When a blob's hunger reaches `HUNGER_SEEK` or thirst reaches `THIRST_SEEK`, and it has a valid memory for the corresponding resource, it will stop wandering and move directly towards the remembered location.
5.  **Seeking Speed:** Movement towards a target occurs at `SEEK_SPEED` pixels per tick.
6.  **Target Priority:** If both hunger and thirst trigger seeking simultaneously, the blob prioritizes the need with the higher value (hunger breaks ties).
7.  **Wandering:** If no seeking condition is met, the blob reverts to random wandering behavior from Phase 1.

## Configuration Parameters

The following parameters were added to `hive_game/hive/config.py`:

*   `HUNGER_SEEK` (int): Hunger threshold to start seeking food.
*   `THIRST_SEEK` (int): Thirst threshold to start seeking water.
*   `MEMORY_SPAN_S` (float): Duration in seconds a memory remains valid.
*   `SEEK_SPEED` (int): Speed in pixels per tick when seeking a target.

## Memory Decay Rationale

Memory decay (`MEMORY_SPAN_S`) prevents blobs from fixating on long-gone resource locations. It encourages exploration when recent memories become stale.
Immediate invalidation when a resource tile is empty ensures blobs don't waste time traveling to a location that is known to be depleted.

## Benchmark Results

*   **Hardware:** [Specify CPU, RAM, OS used for benchmark]
*   **Phase 1 Baseline (1000 blobs):** [Avg frame time] ms
*   **Phase 2 Result (1000 blobs):** [Avg frame time] ms
*   **Delta:** [Phase 2 time - Phase 1 time] ms

*(Note: Benchmark needs to be run and results filled in.)* 