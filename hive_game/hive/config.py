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
BLOB_COUNT: int = 50
BLOB_SIZE: int = 8 # pixels square
BLOB_MAX_NEEDS: int = 255

# Needs rates (per second, adjusted by tick rate in usage)
HUNGER_RATE: float = 1.0
THIRST_RATE: float = 1.0
ENERGY_DECAY: float = 0.5 # Example, less critical for Phase 1

# Resource parameters
FOOD_FILL: int = 120 # Amount hunger decreases when eating
WATER_FILL: int = 120 # Amount thirst decreases when drinking
INITIAL_FOOD_COUNT: int = 40
INITIAL_WATER_COUNT: int = 40
RESOURCE_REGEN_INTERVAL_S: float = 15.0 # Seconds between resource regeneration attempts

# Movement
GRID_STEP: int = 2  # Reduced from BLOB_SIZE (8) to 2 for smoother movement
WANDER_RATE: float = 0.15  # Probability of changing direction each tick

# --- Phase 2 tunables -------------------------------------------------
HUNGER_SEEK: int   = 200    # Start path-seeking if hunger >= X (out of BLOB_MAX_NEEDS)
THIRST_SEEK: int   = 200    # Start path-seeking if thirst >= X (out of BLOB_MAX_NEEDS)
MEMORY_SPAN_S: float = 60.0 # Seconds before a remembered food/water location expires.
SEEK_SPEED: int    = GRID_STEP  # Pixels per tick moved towards target (matched to grid step).

# --- Phase 3 tunables -------------------------------------------------
CHIRP_RADIUS: int = 32         # Hearing distance in pixels.
CHIRP_VOLUME: int = 20         # Max concurrent chirps allowed per frame (rate-limit on emission).
LEXICON_DECAY: float = 0.01    # Fraction weight loss per second without reinforcement.
CONVERGENCE_INTERVAL: int = 5_000 # How often (ticks) to compute global similarity.

# --- Phase 2.5: Reproduction tunables ----------------------------------
REPRO_ENERGY_COST: int = 60    # Energy deducted from each parent.
REPRO_COOLDOWN_S: float = 30.0 # Minimum seconds between reproductions.
MAX_BLOBS: int = 1000         # Maximum allowed blob population.
REPRO_NEARBY_RADIUS: float = 32.0 # Max distance (px) to find a mate.
REPRO_HUNGER_THRESH: int = 80   # Max hunger for reproduction eligibility.
REPRO_THIRST_THRESH: int = 80   # Max thirst for reproduction eligibility.
REPRO_ENERGY_THRESH: int = 200  # Min energy for reproduction eligibility.
ENERGY_GAIN_ON_CONSUME: int = 50 # Energy gained when consuming food/water.

# --- Visual Feedback tunables (Phase 3) --------------------------------
BUBBLE_DURATION_TICKS: int = 60      # How many ticks the action bubble stays visible.
BUBBLE_OFFSET_PX: int = 4         # Vertical offset of the bubble from the blob top.
SHOW_DEBUG_DEFAULT: bool = False    # Whether the debug hover panel is visible by default. 