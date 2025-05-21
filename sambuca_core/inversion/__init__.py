"""Inversion module for deriving water parameters from observed spectra.

This module provides tools to invert the Sambuca forward model, allowing
for the derivation of water column parameters (chlorophyll, CDOM, NAP, depth,
substrate composition) from observed remote sensing reflectance.
"""

from .parameters import InversionParameters
from .objective_functions import spectral_rmse, spectral_angle_mapper, spectral_rmse_with_nedr
from .optimization import invert_spectrum, OptimizationResult, multi_start_inversion
from .lut import LookUpTable
from .pixel_processor import process_pixel, process_image

# Import parallel processing capabilities if available
try:
    from .parallel_processor import parallel_inversion, parallel_minimize
except ImportError:
    # Silently fail if not available
    pass

__all__ = [
    'InversionParameters',
    'spectral_rmse',
    'spectral_angle_mapper',
    'spectral_rmse_with_nedr',
    'invert_spectrum',
    'OptimizationResult',
    'LookUpTable',
    'process_pixel',
    'process_image',
    'multi_start_inversion',
]

# Add parallel processing functions if available
try:
    __all__.extend(['parallel_inversion', 'parallel_minimize'])
except NameError:
    pass