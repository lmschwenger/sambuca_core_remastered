"""Core components of the Sambuca modeling system.

Sambuca is a Semi-Analytical Model for Bathymetry, Un-mixing, and Concentration Assessment
(SAMBUCA) developed by CSIRO for remote sensing applications.
"""

from typing import Tuple, Dict, List

from .forward_model import forward_model, ForwardModelResults

from .siop_manager import SIOPManager

# Optional imports with graceful degradation
try:
    from .data_fetchers import DataFetcherFactory
    _DATA_FETCHERS_AVAILABLE = True
except ImportError:
    _DATA_FETCHERS_AVAILABLE = False
    DataFetcherFactory = None

__author__ = "Lasse M. Schwenger"
__email__ = "lasse.m.schwenger@gmail.com"
__version__ = "0.1.0"

# Type definitions for documentation
Spectra = Tuple[List[float], List[float]]
SpectraDict = Dict[str, Spectra]


def list_data_fetchers() -> Dict[str, dict]:
    """List available data fetchers and their status."""
    if not _DATA_FETCHERS_AVAILABLE:
        return {"error": "Data fetchers module not available"}

    return DataFetcherFactory.get_fetcher_info()


def main():
    """Entry point for command-line usage."""
    print(f"SAMBUCA Core v{__version__}")
    print("Semi-Analytical Model for Bathymetry, Un-mixing, and Concentration Assessment")
    print("")
    print("Usage:")
    print("  sambuca-gui    - Launch the GUI application")
    print("  python -m sambuca.core - Show this help")
    print("")

    # Show data fetcher status
    if _DATA_FETCHERS_AVAILABLE:
        print("Available Data Fetchers:")
        fetchers = list_data_fetchers()
        for name, info in fetchers.items():
            status = "✓" if info.get('available', False) else "✗"
            print(f"  {status} {info.get('name', name)}")
            if not info.get('available', False) and 'dependencies' in info:
                deps = ', '.join(info['dependencies'])
                print(f"    Missing: {deps}")
    else:
        print("Data fetchers not available (optional dependencies not installed)")

    print("")
    print("For more information, see the documentation and examples.")


if __name__ == "__main__":
    main()
