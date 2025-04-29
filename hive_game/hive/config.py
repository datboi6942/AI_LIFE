"""Configuration constants for the HiveLife simulation."""

from __future__ import annotations

# Simulation parameters
TICK_RATE_HZ: int = 60

# Window parameters
WINDOW_WIDTH: int = 600
WINDOW_HEIGHT: int = 600
WINDOW_TITLE: str = "HiveLife v0.1.0 - Phase 1"
BACKGROUND_COLOR: tuple[int, int, int] = (20, 20, 20) # Dark grey

# Blob parameters
BLOB_COUNT: int = 75 # Increased from 50 to 75 for larger gene pool
BLOB_SIZE: int = 8 # pixels square
BLOB_MAX_NEEDS: int = 255

# Needs rates (per second, adjusted by tick rate in usage)
HUNGER_RATE: float = 1.0
THIRST_RATE: float = 1.0
ENERGY_DECAY: float = 0.5 # Example, less critical for Phase 1

# Resource parameters
FOOD_FILL: int = 120 # Amount hunger decreases when eating
WATER_FILL: int = 120 # Amount thirst decreases when drinking
INITIAL_FOOD_COUNT: int = 160 # Doubled from 80 to 160
INITIAL_WATER_COUNT: int = 160 # Doubled from 80 to 160
RESOURCE_REGEN_INTERVAL_S: float = 5.0 # Reduced from 7.5 to 5.0 seconds for faster regeneration

# Movement
GRID_STEP: int = 2  # Reduced from BLOB_SIZE (8) to 2 for smoother movement
WANDER_RATE: float = 0.15  # Probability of changing direction each tick

# --- Phase 2 tunables -------------------------------------------------
HUNGER_SEEK: int   = 100    # Lowered: Start path-seeking if hunger >= X
THIRST_SEEK: int   = 100    # Lowered: Start path-seeking if thirst >= X
MEMORY_SPAN_S: float = 60.0 # Seconds before a remembered food/water location expires.
SEEK_SPEED: int    = GRID_STEP  # Pixels per tick moved towards target (matched to grid step).

# --- Phase 3 tunables -------------------------------------------------
CHIRP_RADIUS: int = 32         # Hearing distance in pixels.
CHIRP_VOLUME: int = 50         # Increased from 20 to 50 to prevent running out of unique chirp IDs
LEXICON_DECAY: float = 0.01    # Fraction weight loss per second without reinforcement.
CONVERGENCE_INTERVAL: int = 5_000 # How often (ticks) to compute global similarity.

# --- Phase 2.5: Reproduction tunables ----------------------------------
ENERGY_MAX: int = 300
ENERGY_REGEN_PER_FOOD: int = 360  # Increased from 200 to 360 for much bigger meal boost
ENERGY_REGEN_PER_WATER: int = 120   # Increased from 80 to 120 for better hydration
REPRO_ENERGY_THRESH: int = 150     # Lowered from 200 to 150 to make reproduction easier
REPRO_ENERGY_COST: int = 50        # Lowered from 80 to 50 to make reproduction cheaper
REPRO_COOLDOWN_S: float = 15.0     # Reduced from 30.0 to 15.0 seconds to allow more frequent reproduction
MAX_BLOBS: int = 500              # Reduced from 1000 to 500 for more manageable population
REPRO_NEARBY_RADIUS: float = 32.0  # Max distance (px) to find a mate
REPRO_HUNGER_THRESH: int = 100     # Increased from 80 to 100 to give more time to find food
REPRO_THIRST_THRESH: int = 100     # Increased from 80 to 100 to give more time to find water
INITIAL_ENERGY: int = 200          # Increased from 150 to 200 for better starting point

# --- Phase 3.5: Lifespan & Exhaustion -----------------------------------
ENERGY_DECAY: float = 0.15        # Reduced from 0.1 to 0.15 for much slower fatigue
EXHAUSTION_GRACE: float = 60.0     # Increased from 30.0 to 60.0 seconds at zero energy before death
MAX_LIFESPAN_S: float = 900        # Increased from 600 to 900 seconds (15 minutes)

# --- Visual Feedback tunables (Phase 3) --------------------------------
BUBBLE_DURATION_TICKS: int = 60      # How many ticks the action bubble stays visible.
BUBBLE_OFFSET_PX: int = 4         # Vertical offset of the bubble from the blob top.
SHOW_DEBUG_DEFAULT: bool = False    # Whether the debug hover panel is visible by default. 