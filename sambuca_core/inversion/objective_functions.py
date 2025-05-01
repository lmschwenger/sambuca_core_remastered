"""Objective functions for the Sambuca inversion process.

This module contains functions that calculate the error between observed and modeled
remote sensing reflectance, which are used as objective functions during optimization.
"""

from typing import List, Optional, Dict, Any, Union

import numpy as np
from numpy.typing import NDArray

from ..forward_model import forward_model


def spectral_rmse(
        params: List[float],
        observed_rrs: NDArray[np.float64],
        inversion_parameters: 'InversionParameters',
        error_weight: Optional[NDArray[np.float64]] = None,
        return_modeled_spectra: bool = False,
) -> Union[float, Dict[str, Any]]:
    """Calculate RMSE between observed and modeled remote sensing reflectance.

    Args:
        params: Optimization parameters (values for the parameters being inverted).
        observed_rrs: Observed remote sensing reflectance.
        inversion_parameters: Parameters for the inversion process.
        error_weight: Optional weights for different wavelengths.
        return_modeled_spectra: If True, return a dictionary with error and modeled spectra.

    Returns:
        Root mean square error between observed and modeled reflectance, or
        a dictionary with error and modeled spectra if return_modeled_spectra is True.
    """
    # Convert params to forward model inputs
    forward_model_params = inversion_parameters.get_forward_model_params(params)

    # Run forward model
    results = forward_model(**forward_model_params)

    # Calculate error
    if error_weight is not None:
        diff_squared = error_weight * (results.rrs - observed_rrs) ** 2
        error = np.sqrt(np.mean(diff_squared))
    else:
        error = np.sqrt(np.mean((results.rrs - observed_rrs) ** 2))

    if return_modeled_spectra:
        return {
            'error': error,
            'modeled_spectra': results.rrs,
            'forward_model_results': results
        }

    return error


def spectral_angle_mapper(
        params: List[float],
        observed_rrs: NDArray[np.float64],
        inversion_parameters: 'InversionParameters',
        return_modeled_spectra: bool = False,
) -> Union[float, Dict[str, Any]]:
    """Calculate spectral angle between observed and modeled spectra.

    This is a measure of spectral shape similarity regardless of intensity.

    Args:
        params: Optimization parameters (values for the parameters being inverted).
        observed_rrs: Observed remote sensing reflectance.
        inversion_parameters: Parameters for the inversion process.
        return_modeled_spectra: If True, return a dictionary with error and modeled spectra.

    Returns:
        Spectral angle in radians, or a dictionary with error and modeled
        spectra if return_modeled_spectra is True.
    """
    # Convert params to forward model inputs
    forward_model_params = inversion_parameters.get_forward_model_params(params)

    # Run forward model
    results = forward_model(**forward_model_params)

    # Calculate spectral angle
    dot_product = np.sum(results.rrs * observed_rrs)
    norm_product = np.sqrt(np.sum(results.rrs ** 2) * np.sum(observed_rrs ** 2))

    # Avoid division by zero
    if norm_product < 1e-10:
        angle = np.pi / 2  # Maximum angle
    else:
        angle = np.arccos(np.clip(dot_product / norm_product, -1.0, 1.0))

    if return_modeled_spectra:
        return {
            'error': angle,
            'modeled_spectra': results.rrs,
            'forward_model_results': results
        }

    return angle


def spectral_relative_rmse(
        params: List[float],
        observed_rrs: NDArray[np.float64],
        inversion_parameters: 'InversionParameters',
        epsilon: float = 1e-6,
        return_modeled_spectra: bool = False,
) -> Union[float, Dict[str, Any]]:
    """Calculate relative RMSE between observed and modeled reflectance.

    This metric is less sensitive to absolute magnitude differences.

    Args:
        params: Optimization parameters (values for the parameters being inverted).
        observed_rrs: Observed remote sensing reflectance.
        inversion_parameters: Parameters for the inversion process.
        epsilon: Small number to avoid division by zero.
        return_modeled_spectra: If True, return a dictionary with error and modeled spectra.

    Returns:
        Relative RMSE between observed and modeled reflectance, or
        a dictionary with error and modeled spectra if return_modeled_spectra is True.
    """
    # Convert params to forward model inputs
    forward_model_params = inversion_parameters.get_forward_model_params(params)

    # Run forward model
    results = forward_model(**forward_model_params)

    # Calculate relative error
    relative_diff = (results.rrs - observed_rrs) / (observed_rrs + epsilon)
    error = np.sqrt(np.mean(relative_diff ** 2))

    if return_modeled_spectra:
        return {
            'error': error,
            'modeled_spectra': results.rrs,
            'forward_model_results': results
        }

    return error


def spectral_chi_square(
        params: List[float],
        observed_rrs: NDArray[np.float64],
        inversion_parameters: 'InversionParameters',
        uncertainty: Optional[NDArray[np.float64]] = None,
        return_modeled_spectra: bool = False,
) -> Union[float, Dict[str, Any]]:
    """Calculate chi-square statistic between observed and modeled reflectance.

    This metric weights the errors by the uncertainty in the measurements.

    Args:
        params: Optimization parameters (values for the parameters being inverted).
        observed_rrs: Observed remote sensing reflectance.
        inversion_parameters: Parameters for the inversion process.
        uncertainty: Uncertainty (standard deviation) for each wavelength.
            If None, a default value of 0.001 is used for all wavelengths.
        return_modeled_spectra: If True, return a dictionary with error and modeled spectra.

    Returns:
        Chi-square statistic, or a dictionary with error and modeled spectra
        if return_modeled_spectra is True.
    """
    # Convert params to forward model inputs
    forward_model_params = inversion_parameters.get_forward_model_params(params)

    # Run forward model
    results = forward_model(**forward_model_params)

    # Set default uncertainty if not provided
    if uncertainty is None:
        uncertainty = np.full_like(observed_rrs, 0.001)

    # Calculate chi-square
    chi_square = np.sum(((results.rrs - observed_rrs) / uncertainty) ** 2)

    if return_modeled_spectra:
        return {
            'error': chi_square,
            'modeled_spectra': results.rrs,
            'forward_model_results': results
        }

    return chi_square