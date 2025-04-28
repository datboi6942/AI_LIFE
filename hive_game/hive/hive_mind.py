from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, List, Optional, Set, Tuple

if TYPE_CHECKING:
    from hive_game.hive.blob import Blob

# Configure logging if not already configured elsewhere
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def calculate_jaccard_similarity(set1: Set[int], set2: Set[int]) -> float:
    """Calculates the Jaccard similarity between two sets of integers."""
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    if union == 0:
        return 1.0  # Both sets are empty, consider them identical
    else:
        return intersection / union


def update_convergence(
    blobs: List[Blob],
    current_tick: int,
    interval: int,
    dominant_threshold: float = 0.6
) -> Optional[float]:
    """
    Calculates and logs the average Jaccard similarity of blob lexicons
    at the specified interval.

    Args:
        blobs: The list of all active blobs.
        current_tick: The current simulation tick.
        interval: How often (in ticks) to calculate convergence.
        dominant_threshold: The minimum weight for a chirp to be considered 'dominant'.

    Returns:
        The average Jaccard similarity if calculated, otherwise None.
    """
    if not blobs or current_tick % interval != 0:
        return None

    dominant_sets_food: List[Set[int]] = []
    dominant_sets_water: List[Set[int]] = []

    for blob in blobs:
        blob_food_set: Set[int] = set()
        blob_water_set: Set[int] = set()
        # Check if blob has lexicon attribute defensively
        if hasattr(blob, 'lexicon') and blob.lexicon:
            for chirp_id, concepts in blob.lexicon.items():
                if concepts.get("food", 0.0) >= dominant_threshold:
                    blob_food_set.add(chirp_id)
                if concepts.get("water", 0.0) >= dominant_threshold:
                    blob_water_set.add(chirp_id)
        dominant_sets_food.append(blob_food_set)
        dominant_sets_water.append(blob_water_set)

    total_jaccard_food = 0.0
    total_jaccard_water = 0.0
    pair_count = 0

    num_blobs = len(blobs)
    if num_blobs < 2:
        # Cannot compare pairs if fewer than 2 blobs
        avg_jaccard_food = 1.0
        avg_jaccard_water = 1.0
    else:
        for i in range(num_blobs):
            for j in range(i + 1, num_blobs):
                jaccard_food = calculate_jaccard_similarity(dominant_sets_food[i], dominant_sets_food[j])
                jaccard_water = calculate_jaccard_similarity(dominant_sets_water[i], dominant_sets_water[j])
                total_jaccard_food += jaccard_food
                total_jaccard_water += jaccard_water
                pair_count += 1
        
        # Handle division by zero if pair_count is somehow 0 (shouldn't happen if num_blobs >= 2)
        avg_jaccard_food = (total_jaccard_food / pair_count) if pair_count > 0 else 1.0
        avg_jaccard_water = (total_jaccard_water / pair_count) if pair_count > 0 else 1.0

    overall_avg = (avg_jaccard_food + avg_jaccard_water) / 2.0

    log.info(
        f"Tick {current_tick}: Convergence Check - Blobs={num_blobs}, Pairs={pair_count}, "
        f"Food Jaccard={avg_jaccard_food:.3f}, Water Jaccard={avg_jaccard_water:.3f}, "
        f"Avg Jaccard={overall_avg:.3f}"
    )

    return overall_avg 