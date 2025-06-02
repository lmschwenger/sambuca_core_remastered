"""Core components of the Sambuca modeling system.

Sambuca is a Semi-Analytical Model for Bathymetry, Un-mixing, and Concentration Assessment
(SAMBUCA) developed by CSIRO for remote sensing applications.
"""

from typing import Tuple, Dict, List

from .exceptions import (
    SambucaException,
    UnsupportedDataFormatError,
    DataValidationError,
)
from .forward_model import forward_model, ForwardModelResults

from .siop_manager import SIOPManager

from .utility import (
    strictly_decreasing,
    strictly_increasing,
)

__author__ = "Lasse M. Schwenger"
__email__ = "lasse.m.schwenger@gmail.com"
__version__ = "0.1.0"

# Type definitions for documentation
Spectra = Tuple[List[float], List[float]]
SpectraDict = Dict[str, Spectra]


def main():
    """Entry point for command-line usage."""
    print(f"SAMBUCA Core v{__version__}")
    print("Semi-Analytical Model for Bathymetry, Un-mixing, and Concentration Assessment")
    print("")
    print("Usage:")
    print("  sambuca-gui    - Launch the GUI application")
    print("  python -m sambuca_core - Show this help")
    print("")
    print("For more information, see the documentation and examples.")


if __name__ == "__main__":
    main()