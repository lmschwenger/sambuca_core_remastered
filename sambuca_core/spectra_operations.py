"""Functions for manipulating spectra tuples.

This module contains functions for working with spectra represented as
(wavelength, value) tuples.
"""

from typing import Sequence, Tuple, Union

import numpy as np
from numpy.typing import NDArray


def spectra_find_common_wavelengths(*args: Union[Sequence, Tuple]) -> NDArray[np.float64]:
    """Finds the common subset of wavelengths for the given inputs.

    Args:
        *args: A sequence of wavelength values, or a tuple of (wavelength, values).

    Returns:
        The common subset of wavelengths, which can be used as an
        input to spectra_apply_wavelength_mask.

    Raises:
        ValueError: If no arguments are provided.
    """
    if not args:
        raise ValueError("At least one argument must be provided")

    # Extract wavelengths from inputs
    wavelengths = []
    for arg in args:
        if isinstance(arg, tuple) and len(arg) >= 1:
            # Extract wavelengths from (wavelength, values) tuple
            wavelengths.append(arg[0])
        else:
            # Assume the argument itself is wavelengths
            wavelengths.append(arg)

    # Find common wavelengths
    if wavelengths:
        common = wavelengths[0]
        for w in wavelengths[1:]:
            common = np.intersect1d(common, w)
        return common
    else:
        raise ValueError("Invalid arguments")


def spectra_apply_wavelength_mask(
    spectra: Tuple[NDArray[np.float64], NDArray[np.float64]],
    mask: NDArray[np.float64]
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Applies a wavelength mask to a spectra.

    All values in the spectra that are not in the mask will be removed in the
    returned values. The input spectra is not modified.

    Args:
        spectra: The (wavelengths, values) spectra tuple.
        mask: The wavelength values that should be retained.

    Returns:
        The masked tuple of (wavelengths, values).
    """
    boolean_mask = (spectra[0] >= mask.min()) & (spectra[0] <= mask.max())
    return spectra[0][boolean_mask], spectra[1][boolean_mask]