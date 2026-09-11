"""
Duplicate Detection Module.
Detects duplicate weather reports and social posts using:
1. Perceptual Image Hash comparison (Hamming distance threshold)
2. Text similarity matching (Cosine similarity / Jaccard index)
3. Geo-temporal proximity matching
"""
import math
from typing import Optional, List, Tuple
from datetime import datetime, timedelta

try:
    import imagehash
except ImportError:
    imagehash = None


def is_duplicate_hash(hash1: str, hash2: str, max_distance: int = 5) -> bool:
    """Checks if two image hex hashes are duplicates within Hamming distance."""
    if not hash1 or not hash2:
        return False
    if hash1 == hash2:
        return True
    if imagehash is not None:
        try:
            h1 = imagehash.hex_to_hash(hash1)
            h2 = imagehash.hex_to_hash(hash2)
            return (h1 - h2) <= max_distance
        except Exception:
            pass
    return hash1 == hash2


def text_similarity(text1: str, text2: str) -> float:
    """Calculates word-level Jaccard similarity between two texts."""
    if not text1 or not text2:
        return 0.0
    w1 = set(text1.lower().split())
    w2 = set(text2.lower().split())
    if not w1 or not w2:
        return 0.0
    intersection = len(w1.intersection(w2))
    union = len(w1.union(w2))
    return intersection / union if union > 0 else 0.0


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def is_spatial_temporal_duplicate(
    lat1: float, lon1: float, time1: datetime,
    lat2: float, lon2: float, time2: datetime,
    max_radius_km: float = 15.0,
    max_time_diff_hours: float = 3.0
) -> bool:
    """Checks if two reports refer to the exact same incident in space & time."""
    time_diff = abs((time1 - time2).total_seconds()) / 3600.0
    if time_diff > max_time_diff_hours:
        return False
    distance = calculate_haversine_distance(lat1, lon1, lat2, lon2)
    return distance <= max_radius_km
