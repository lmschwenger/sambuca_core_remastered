import numpy as np
from typing import Tuple


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers using Haversine formula."""
    R = 6371  # Earth's radius in km

    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (np.sin(dlat / 2) * np.sin(dlat / 2) +
         np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) *
         np.sin(dlon / 2) * np.sin(dlon / 2))
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c


def create_bbox(lat: float, lon: float, buffer_km: float) -> Tuple[float, float, float, float]:
    """Create bounding box around a point.

    Returns:
        Tuple of (west, south, east, north) in decimal degrees
    """
    lat_buffer = buffer_km / 111.0  # Rough km to degrees conversion
    lon_buffer = buffer_km / (111.0 * np.cos(np.radians(lat)))

    return (
        lon - lon_buffer,  # West
        lat - lat_buffer,  # South
        lon + lon_buffer,  # East
        lat + lat_buffer  # North
    )