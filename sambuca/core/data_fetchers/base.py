"""Base classes for data fetchers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path


class BaseDataFetcher(ABC):
    """Abstract base class for data fetchers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Fetcher name."""
        pass

    @property
    @abstractmethod
    def supported_parameters(self) -> List[str]:
        """List of supported parameters that can be fetched."""
        pass

    @property
    @abstractmethod
    def required_dependencies(self) -> List[str]:
        """List of required Python packages for this fetcher."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the fetcher is available (dependencies installed)."""
        pass

    @abstractmethod
    def fetch_data(self, 
                   aoi: str, 
                   date: str, 
                   parameters: List[str] = None,
                   output_dir: Optional[str] = None,
                   **kwargs) -> Dict[str, str]:
        """
        Fetch data for the given area of interest and date.
        
        Args:
            aoi: Area of Interest (format depends on fetcher)
            date: Target date in YYYY-MM-DD format
            parameters: List of parameters to fetch
            output_dir: Directory to save files
            **kwargs: Additional fetcher-specific arguments
            
        Returns:
            Dictionary mapping parameter names to saved file paths
        """
        pass

    def validate_parameters(self, parameters: List[str]) -> None:
        """Validate that requested parameters are supported."""
        if parameters:
            unsupported = set(parameters) - set(self.supported_parameters)
            if unsupported:
                supported = ', '.join(self.supported_parameters)
                raise ValueError(f"Unsupported parameters: {unsupported}. "
                               f"Supported: {supported}")
