"""SAMBUCA Utilities Package.

This package provides utility functions and modules for SAMBUCA
(Semi-Analytical Model for Bathymetry, Un-mixing, and Concentration Assessment).
"""

__version__ = "0.1.0"
__author__ = "Lasse M. Schwenger"
__email__ = "lasse.m.schwenger@gmail.com"

# Import main utility modules for convenience
from . import data_fetchers
from . import visualization

__all__ = ["data_fetchers", "visualization"]
