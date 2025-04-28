"""Resource types that can be present on tiles in the world."""
from __future__ import annotations

import enum

class ResourceType(enum.IntEnum):
    """Types of resources that can be present on tiles."""
    EMPTY = 0
    FOOD = 1
    WATER = 2 