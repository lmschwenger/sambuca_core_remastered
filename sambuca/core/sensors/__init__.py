from typing import List

from .base import BaseSensor
from .sentinel2 import Sentinel2Sensor


class SensorFactory:
    """Factory for creating sensor instances."""

    _sensors = {
        'sentinel2': Sentinel2Sensor,
        's2': Sentinel2Sensor,  # Alias
    }

    @classmethod
    def create(cls, sensor_name: str) -> BaseSensor:
        """Create a sensor instance by name."""
        sensor_name = sensor_name.lower()
        if sensor_name not in cls._sensors:
            available = ', '.join(cls._sensors.keys())
            raise ValueError(f"Unknown sensor '{sensor_name}'. Available: {available}")

        return cls._sensors[sensor_name]()

    @classmethod
    def list_available(cls) -> List[str]:
        """List available sensor names."""
        return list(cls._sensors.keys())


__all__ = ['BaseSensor', 'Sentinel2Sensor', 'SensorFactory']