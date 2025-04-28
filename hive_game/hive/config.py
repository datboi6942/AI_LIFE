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

# Movement
GRID_STEP: int = BLOB_SIZE # Move one blob size at a time 

# --- Phase 2 tunables -------------------------------------------------
HUNGER_SEEK: int   = 200    # start path-seeking if hunger >= X
THIRST_SEEK: int   = 200
MEMORY_SPAN_S: float = 60.0     # seconds before a memory entry expires
SEEK_SPEED: int    = GRID_STEP  # px per tick (ensure it's same as grid step for Phase 2) 