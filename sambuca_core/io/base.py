from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Any, Dict

import numpy as np
from numpy.typing import NDArray


@dataclass
class ImageData:
    """Container for loaded image data and metadata."""
    data: NDArray[np.float32]  # Shape: (height, width, bands) or (bands, height, width)
    metadata: Dict[str, Any]
    filepath: str
    bands: Optional[List[str]] = None
    wavelengths: Optional[List[float]] = None

    @property
    def shape(self):
        return self.data.shape

    @property
    def is_bands_last(self) -> bool:
        """Check if bands are the last dimension."""
        return len(self.shape) == 3 and self.shape[2] <= self.shape[0]


class BaseImageLoader(ABC):
    """Abstract base class for image loaders."""

    @abstractmethod
    def load(self, filepath: str, bands: Optional[List] = None) -> ImageData:
        """Load image from file."""
        pass
