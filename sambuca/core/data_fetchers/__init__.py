"""Data fetchers for external data sources."""

from typing import List, Optional

from .base import BaseDataFetcher


class DataFetcherFactory:
    """Factory for creating data fetcher instances."""

    _fetchers = {}

    @classmethod
    def _register_sentinel3(cls):
        """Register Sentinel-3 fetcher if available."""
        try:
            from .sentinel3 import Sentinel3DataFetcher
            cls._fetchers.update({
                'sentinel3': Sentinel3DataFetcher,
                's3': Sentinel3DataFetcher,  # Alias
                'sentinel-3': Sentinel3DataFetcher,  # Alias
            })
        except ImportError:
            pass  # Sentinel-3 dependencies not available

    @classmethod
    def _ensure_registered(cls):
        """Ensure all available fetchers are registered."""
        if not cls._fetchers:
            cls._register_sentinel3()

    @classmethod
    def create(cls, fetcher_name: str, **kwargs) -> BaseDataFetcher:
        """
        Create a data fetcher instance by name.
        
        Args:
            fetcher_name: Name of the fetcher
            **kwargs: Arguments to pass to the fetcher constructor
            
        Returns:
            Data fetcher instance
            
        Raises:
            ValueError: If fetcher is unknown or dependencies not available
        """
        cls._ensure_registered()
        
        fetcher_name = fetcher_name.lower()
        if fetcher_name not in cls._fetchers:
            available = ', '.join(cls._fetchers.keys()) if cls._fetchers else 'none'
            raise ValueError(f"Unknown data fetcher '{fetcher_name}'. Available: {available}")

        fetcher_class = cls._fetchers[fetcher_name]
        fetcher = fetcher_class(**kwargs)
        
        # Check if fetcher is actually available
        if not fetcher.is_available():
            deps = ', '.join(fetcher.required_dependencies)
            raise ValueError(f"Data fetcher '{fetcher_name}' requires missing dependencies: {deps}")
        
        return fetcher

    @classmethod
    def list_available(cls) -> List[str]:
        """List available data fetcher names."""
        cls._ensure_registered()
        return list(cls._fetchers.keys())

    @classmethod
    def get_fetcher_info(cls, fetcher_name: Optional[str] = None) -> dict:
        """
        Get information about available data fetchers.
        
        Args:
            fetcher_name: Specific fetcher name, or None for all
            
        Returns:
            Dictionary with fetcher information
        """
        cls._ensure_registered()
        
        info = {}
        
        if fetcher_name:
            fetcher_name = fetcher_name.lower()
            if fetcher_name in cls._fetchers:
                try:
                    fetcher = cls._fetchers[fetcher_name]()
                    info[fetcher_name] = {
                        'name': fetcher.name,
                        'available': fetcher.is_available(),
                        'parameters': fetcher.supported_parameters,
                        'dependencies': fetcher.required_dependencies
                    }
                except Exception:
                    info[fetcher_name] = {
                        'name': fetcher_name,
                        'available': False,
                        'error': 'Failed to initialize'
                    }
        else:
            for name, fetcher_class in cls._fetchers.items():
                try:
                    fetcher = fetcher_class()
                    info[name] = {
                        'name': fetcher.name,
                        'available': fetcher.is_available(),
                        'parameters': fetcher.supported_parameters,
                        'dependencies': fetcher.required_dependencies
                    }
                except Exception:
                    info[name] = {
                        'name': name,
                        'available': False,
                        'error': 'Failed to initialize'
                    }
        
        return info


# Export base class for custom fetchers
__all__ = ['BaseDataFetcher', 'DataFetcherFactory']
