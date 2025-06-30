from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any


class BaseWorkflow(ABC):
    """Abstract base class for processing workflows."""

    def __init__(self, siop_dir: str, sensor: str = 'sentinel2'):
        """
        Initialize workflow.

        Args:
            siop_dir: Path to SIOP directory
            sensor: Sensor name (e.g., 'sentinel2', 'landsat8')
        """
        self.siop_dir = Path(siop_dir)
        self.sensor_name = sensor
        self._setup_components()
        self._setup_defaults()

    @abstractmethod
    def _setup_defaults(self):
        """Set up default parameters for this workflow type."""
        pass

    def _setup_components(self):
        """Initialize common components."""
        from sambuca.core.siop_manager import SIOPManager
        from sambuca_utils.io import RasterImageLoader

        self.siop_manager = SIOPManager(str(self.siop_dir))
        self.image_loader = RasterImageLoader()

    def get_config(self) -> Dict[str, Any]:
        """Get the current workflow configuration."""
        return {
            'workflow_type': self.__class__.__name__,
            'sensor': self.sensor_name,
            'bands': getattr(self, 'bands', None),
            'wavelengths': getattr(self, 'wavelengths', None),
            'inversion_params': getattr(self, 'inversion_params', None)
        }
