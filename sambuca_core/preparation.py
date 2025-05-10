# sambuca_core/__init__.py (or a new module like preparation.py)
from typing import Tuple, List

import numpy as np
from numpy._typing import NDArray


def prepare_spectral_inputs(
        wavelengths: NDArray[np.float64],
        sensor_filter: Tuple[NDArray[np.float64], NDArray[np.float64]],
        spectra_list: List[Tuple[NDArray[np.float64], NDArray[np.float64]]],
        truncate_filter: bool = True
) -> Tuple[
    NDArray[np.float64],
    Tuple[NDArray[np.float64], NDArray[np.float64]],
    List[Tuple[NDArray[np.float64], NDArray[np.float64]]]
]:
    """Prepares spectral inputs by finding common wavelengths and truncating as needed.

    This function handles the process of finding common wavelengths among
    all spectral inputs, masking spectral data to those wavelengths, and
    optionally truncating the sensor filter to match.

    Args:
        wavelengths: Initial wavelengths to consider, or None to derive from inputs.
        sensor_filter: The sensor filter as (wavelengths, filter_response).
        spectra_list: List of spectral data as (wavelengths, values) tuples.
        truncate_filter: Whether to truncate the sensor filter to match common wavelengths.

    Returns:
        Tuple containing:
            - Common wavelengths array
            - Truncated/processed sensor filter
            - List of masked spectral data
    """
    from .spectra_operations import spectra_find_common_wavelengths, spectra_apply_wavelength_mask
    from .sensor_filter import truncate_filter_to_wavelengths

    # Find common wavelength range among all inputs
    all_inputs = [sensor_filter[0]] + [spectra[0] for spectra in spectra_list]
    if wavelengths is None:
        wavelengths = spectra_find_common_wavelengths(*all_inputs)

    # Apply the wavelength mask to all spectral data
    masked_spectra = []
    for spectra in spectra_list:
        masked_spectra.append(spectra_apply_wavelength_mask(spectra, wavelengths))

    # Truncate the sensor filter if requested
    processed_filter = sensor_filter
    if truncate_filter:
        processed_filter = truncate_filter_to_wavelengths(sensor_filter, wavelengths)

    return wavelengths, processed_filter, masked_spectra