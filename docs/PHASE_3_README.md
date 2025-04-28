# Phase 3: Communication & Collective Intelligence

This phase focuses on enabling blobs to communicate basic concepts (food/water locations)
through procedurally generated chirps and learn a shared lexicon.

## Goals

*   Implement chirp generation and playback (`hive/sound.py`).
*   Enable blobs to broadcast chirps upon finding resources (`blob.py`).
*   Allow blobs to hear nearby chirps and store them with a contextual guess (`blob.py`).
*   Implement reinforcement learning: strengthen chirp-concept associations upon successful prediction, weaken upon failure/timeout (`blob.py`).
*   Add lexicon decay over time (`blob.py`).
*   Introduce a global convergence metric (Jaccard similarity) to track lexicon alignment (`hive_mind.py`).
*   Implement Action-Feedback Overlay (Bubbles + Debug Panel).

## APIs

*   `sound.get_or_generate_sound(chirp_id)`: Returns/creates `arcade.Sound`.
*   `sound.play_chirp(chirp_id, game_window)`: Plays the sound.
*   `blob._broadcast_discovery(concept, current_tick, events)`
*   `blob._process_heard_chirps(events, current_tick)`
*   `blob._apply_positive_reinforcement(consumed_concept)`
*   `blob._process_reinforcement_queue(current_tick)`
*   `blob._decay_lexicon(dt)`
*   `hive_mind.update_convergence(...)`
*   `game_window._draw_bubble(blob)`
*   `game_window._draw_debug_panel(blob)`

## Performance Budgets

*   Chirp generation should be fast enough not to block significantly.
*   Lexicon updates and decay should be O(N_blobs * avg_lexicon_size).
*   Convergence calculation can be O(N_blobs^2 * avg_lexicon_size) but only runs infrequently (e.g., every 5000 ticks).
*   Drawing bubbles/debug panel should add negligible overhead.

## Visual Feedback

*   **Action Bubbles:** When a blob successfully broadcasts a chirp (finds food/water and isn't rate-limited), a small square bubble appears briefly above its head.
    *   Green Square: Indicates a chirp related to finding food.
    *   Blue Square: Indicates a chirp related to finding water.
    *   The bubble lasts for `BUBBLE_DURATION_TICKS` (default 60).
*   **Debug Panel:** Pressing `F2` toggles a debug overlay. When active, hovering the mouse over a blob displays a panel in the top-left corner showing:
    *   Blob ID
    *   Current Hunger, Thirst, Energy levels.
    *   Current target (Wandering, FOOD(x,y), or WATER(x,y)).
    *   Top 3 entries from the blob's lexicon (ChirpID ▶ Concept(Weight)).

*(Screenshot Placeholder: Add an image showing a blob with a bubble and the debug panel active)* 