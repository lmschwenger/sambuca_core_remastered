"""Inversion module for deriving water parameters from observed spectra.

This module provides tools to invert the Sambuca forward model, allowing
for the derivation of water column parameters (chlorophyll, CDOM, NAP, depth,
substrate composition) from observed remote sensing reflectance.
"""

from .parameters import InversionParameters
from .objective_functions import spectral_rmse, spectral_angle_mapper
from .optimization import invert_spectrum, OptimizationResult, multi_start_inversion
from .lut import LookUpTable
from .pixel_processor import process_pixel, process_image
from .robust_inversion import (
    robust_invert_spectrum,
    multi_substrate_inversion,
    spectral_angle_f_metric
)

__all__ = [
    'InversionParameters',
    'spectral_rmse',
    'spectral_angle_mapper',
    'invert_spectrum',
    'OptimizationResult',
    'LookUpTable',
    'process_pixel',
    'process_image',
    'robust_invert_spectrum',
    'multi_substrate_inversion',
    'spectral_angle_f_metric'
]