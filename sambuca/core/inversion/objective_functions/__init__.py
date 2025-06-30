"""Objective functions for SAMBUCA inversion.

This module provides class-based objective functions for comparing observed
and modeled remote sensing reflectance during inversion.

Each objective function is implemented as a separate class in its own file,
following the single responsibility principle.
"""

# Import base classes
from .base import ObjectiveFunction, ForwardModelObjectiveFunction

# Import all objective function classes
from .spectral_rmse import SpectralRMSE
from .spectral_angle_mapper import SpectralAngleMapper
from .spectral_rmse_with_nedr import SpectralRMSEWithNEDR
from .spectral_relative_rmse import SpectralRelativeRMSE
from .spectral_chi_square import SpectralChiSquare

# Export all classes
__all__ = [
    # Base classes
    'ObjectiveFunction',
    'ForwardModelObjectiveFunction',
    
    # Specific objective functions
    'SpectralRMSE',
    'SpectralAngleMapper', 
    'SpectralRMSEWithNEDR',
    'SpectralRelativeRMSE',
    'SpectralChiSquare',
]


# Convenience factory functions for creating commonly used objective functions
def create_rmse(error_weight=None):
    """Create a standard RMSE objective function.
    
    Args:
        error_weight: Optional weights for different wavelengths.
        
    Returns:
        SpectralRMSE instance.
    """
    return SpectralRMSE(error_weight=error_weight)


def create_rmse_with_nedr(nedr=None):
    """Create an NEDR-weighted RMSE objective function.
    
    Args:
        nedr: NEDR values for each band.
        
    Returns:
        SpectralRMSEWithNEDR instance.
    """
    return SpectralRMSEWithNEDR(nedr=nedr)


def create_angle_mapper():
    """Create a spectral angle mapper objective function.
    
    Returns:
        SpectralAngleMapper instance.
    """
    return SpectralAngleMapper()


def create_relative_rmse(epsilon=1e-6):
    """Create a relative RMSE objective function.
    
    Args:
        epsilon: Small number to avoid division by zero.
        
    Returns:
        SpectralRelativeRMSE instance.
    """
    return SpectralRelativeRMSE(epsilon=epsilon)


def create_chi_square(uncertainty=None):
    """Create a chi-square objective function.
    
    Args:
        uncertainty: Uncertainty values for each wavelength.
        
    Returns:
        SpectralChiSquare instance.
    """
    return SpectralChiSquare(uncertainty=uncertainty)
