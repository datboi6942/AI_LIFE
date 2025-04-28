# Phase 1: Core Survival Loop - Design & Performance Notes

**Version:** v0.1.0

## Goals

Implement the absolute minimum required for blobs to exist, move randomly, consume resources (food/water), and die from starvation or dehydration.

- **Window:** 600x600 Arcade window.
- **Entities:** 50 Blob agents (8x8 pixels).
- **World:** Simple dictionary-based grid for FOOD and WATER tiles.
- **Needs:** Hunger and Thirst increase over time, decrease on consumption.
- **Death:** Blobs with hunger or thirst >= 255 are marked `alive=False` and stop updating/drawing.
- **Movement:** Random walk (±1 grid step per tick).
- **HUD:** Basic FPS and live blob count.

## Key Implementation Details

- **Configuration:** Tunable parameters (counts, rates) are centralized in `hive/config.py`.
- **World Grid:** Uses a dictionary `{(x, y): ResourceType}`. Pixel coordinates are snapped to the grid (`config.GRID_STEP`) for lookups and consumption.
- **Blob State:** Managed within the `Blob` dataclass.
- **Update Loop:** `GameWindow.on_update` iterates through all blobs, calling `blob.update()`. Dead blobs skip updates.
- **Drawing:** `GameWindow.on_draw` clears the screen, draws resource tiles using `arcade.ShapeElementList` for basic batching, draws blobs, and renders the HUD text.

## Performance Notes

- **Target:** `< 2 ms` total `on_update` time for 50 blobs.
- **Allocations:** Care was taken to avoid significant memory allocations within the main `blob.update` loop (e.g., no new lists/dicts created per blob per frame).
- **Drawing:** Resource drawing uses `ShapeElementList`. Blob drawing iterates and calls `arcade.draw_rectangle_filled`. At 50 blobs, this is expected to be well within budget.
- **Future Scaling:** If blob count increases significantly, optimizations like spatial hashing for resource lookups, batched drawing (SpriteLists), or slice-updating might be needed. 