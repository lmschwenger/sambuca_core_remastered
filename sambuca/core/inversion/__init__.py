"""Inversion module for deriving water parameters from observed spectra.

This module provides tools to invert the Sambuca forward model, allowing
for the derivation of water column parameters (chlorophyll, CDOM, NAP, depth,
substrate composition) from observed remote sensing reflectance.
"""

from .parameters import InversionParameters
from .objective_functions import (
    ObjectiveFunction,
    ForwardModelObjectiveFunction,
    SpectralRMSE,
    SpectralAngleMapper,
    SpectralRMSEWithNEDR,
    SpectralRelativeRMSE,
    SpectralChiSquare
)
from .optimization import invert_spectrum, multi_start_inversion
from .optimization_result import OptimizationResult
from .lut import LookUpTable
from .pixel_processor import process_pixel, process_image, batch_process_image

__all__ = [
    'InversionParameters',
    'ObjectiveFunction',
    'ForwardModelObjectiveFunction',
    'SpectralRMSE',
    'SpectralAngleMapper',
    'SpectralRMSEWithNEDR',
    'SpectralRelativeRMSE',
    'SpectralChiSquare',
    'invert_spectrum',
    'OptimizationResult',
    'LookUpTable',
    'process_pixel',
    'process_image',
    'batch_process_image',
    'multi_start_inversion'
]
