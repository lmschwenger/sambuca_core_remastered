# sensor_filter.py

"""Functions for working with Sensor Filters and spectral interpolation."""

import numpy as np
from typing import Tuple, List, Dict, Optional, Union, Any
from numpy.typing import NDArray

def truncate_filter_to_wavelengths(
    sensor_filter: Tuple[NDArray[np.float64], NDArray[np.float64]],
    wavelengths: NDArray[np.float64]
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Truncates a sensor filter to match the given wavelength range.
    
    This function ensures that the sensor filter only includes response values
    within the common wavelength range of the input data. This is important
    for consistent processing of spectral data from different sources.
    
    Args:
        sensor_filter: A tuple containing (wavelengths, filter_response) where
            filter_response is a 2D array with shape (n_bands, n_wavelengths).
        wavelengths: The target wavelength range to which the filter should be truncated.
            
    Returns:
        A tuple containing the truncated (wavelengths, filter_response).
    """
    # Get the wavelengths and response matrix from the filter
    filter_wavelengths, filter_response = sensor_filter
    
    # Create a mask for wavelengths within the target range
    mask = (filter_wavelengths >= wavelengths.min()) & (filter_wavelengths <= wavelengths.max())
    
    # Apply the mask to both wavelengths and response matrix
    truncated_wavelengths = filter_wavelengths[mask]
    truncated_response = filter_response[:, mask]
    
    return truncated_wavelengths, truncated_response

def interpolate_filter_to_wavelengths(
    sensor_filter: Tuple[NDArray[np.float64], NDArray[np.float64]],
    target_wavelengths: NDArray[np.float64]
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Interpolates a sensor filter to a new set of wavelengths.
    
    Instead of just truncating the filter, this function resamples the filter
    response to exactly match the target wavelength values using linear interpolation.
    
    Args:
        sensor_filter: A tuple containing (wavelengths, filter_response) where
            filter_response is a 2D array with shape (n_bands, n_wavelengths).
        target_wavelengths: The target wavelengths to interpolate to.
            
    Returns:
        A tuple containing the interpolated (wavelengths, filter_response).
    """
    from scipy.interpolate import interp1d
    
    # Get the wavelengths and response matrix from the filter
    filter_wavelengths, filter_response = sensor_filter
    
    # Check if target wavelengths are within filter wavelength range
    if target_wavelengths.min() < filter_wavelengths.min() or target_wavelengths.max() > filter_wavelengths.max():
        raise ValueError(
            f"Target wavelengths ({target_wavelengths.min()}-{target_wavelengths.max()}) "
            f"are outside the filter wavelength range ({filter_wavelengths.min()}-{filter_wavelengths.max()})"
        )
    
    # Create interpolated response for each band
    interpolated_response = np.zeros((filter_response.shape[0], len(target_wavelengths)))
    
    for i in range(filter_response.shape[0]):
        interpolator = interp1d(filter_wavelengths, filter_response[i, :], kind='linear')
        interpolated_response[i, :] = interpolator(target_wavelengths)
    
    return target_wavelengths, interpolated_response

def normalize_filter_response(
    sensor_filter: Tuple[NDArray[np.float64], NDArray[np.float64]],
    method: str = 'max'
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Normalizes the filter response values.
    
    Args:
        sensor_filter: A tuple containing (wavelengths, filter_response) where
            filter_response is a 2D array with shape (n_bands, n_wavelengths).
        method: Normalization method, either 'max' (normalize each band by its maximum)
            or 'sum' (normalize each band to sum to 1.0).
            
    Returns:
        A tuple containing the original wavelengths and normalized filter response.
    """
    # Get the wavelengths and response matrix from the filter
    wavelengths, filter_response = sensor_filter
    
    # Create a copy of the response to avoid modifying the original
    normalized_response = filter_response.copy()
    
    # Normalize each band
    for i in range(filter_response.shape[0]):
        if method == 'max':
            normalizer = np.max(filter_response[i, :])
            if normalizer > 0:
                normalized_response[i, :] /= normalizer
        elif method == 'sum':
            normalizer = np.sum(filter_response[i, :])
            if normalizer > 0:
                normalized_response[i, :] /= normalizer
        else:
            raise ValueError(f"Unknown normalization method: {method}")
    
    return wavelengths, normalized_response

def validate_sensor_filter(
    sensor_filter: Tuple[NDArray[np.float64], NDArray[np.float64]]
) -> bool:
    """Validates that a sensor filter has the correct format and values.
    
    Args:
        sensor_filter: A tuple containing (wavelengths, filter_response) where
            filter_response is a 2D array with shape (n_bands, n_wavelengths).
            
    Returns:
        True if the filter is valid, False otherwise.
    """
    # Get the wavelengths and response matrix from the filter
    wavelengths, filter_response = sensor_filter
    
    # Check that wavelengths is a 1D array
    if wavelengths.ndim != 1:
        return False
    
    # Check that filter_response is a 2D array
    if filter_response.ndim != 2:
        return False
    
    # Check that the number of wavelengths matches the second dimension of filter_response
    if len(wavelengths) != filter_response.shape[1]:
        return False
    
    # Check that wavelengths are monotonically increasing
    if not np.all(np.diff(wavelengths) > 0):
        return False
    
    # Check that filter response values are non-negative
    if np.any(filter_response < 0):
        return False
    
    return True

def apply_sensor_filter_with_validation(
    spectra: Union[NDArray[np.float64], List[float]],
    sensor_filter: Tuple[NDArray[np.float64], NDArray[np.float64]],
    validate: bool = True
) -> NDArray[np.float64]:
    """Applies a sensor filter to spectra with optional validation.
    
    This is an enhanced version of the core apply_sensor_filter function
    that includes validation steps to ensure the inputs are correctly formatted.
    
    Args:
        spectra: The input spectra as a 1D array or list for a single spectrum,
            or a 2D array where each column is a separate spectrum.
        sensor_filter: A tuple containing (wavelengths, filter_response) where
            filter_response is a 2D array with shape (n_bands, n_wavelengths).
        validate: Whether to validate the sensor filter before applying.
            
    Returns:
        The filtered spectra.
        
    Raises:
        ValueError: If validation is enabled and the sensor filter is invalid.
    """
    # Convert to numpy array if needed
    spectra_arr = np.asarray(spectra)
    
    # Validate the sensor filter if requested
    if validate and not validate_sensor_filter(sensor_filter):
        raise ValueError("Invalid sensor filter format or values")
    
    # Extract the filter response
    _, filter_response = sensor_filter
    
    # Check if input is 2D (multiple spectra)
    if spectra_arr.ndim > 1:
        # For 2D input, each column is a separate spectrum
        # Output will be a 2D array with shape (n_output_bands, n_spectra)
        result = np.dot(
            filter_response, spectra_arr
        ) / filter_response.sum(axis=1, keepdims=True)
        return result
    else:
        # For 1D input (single spectrum), output will be a 1D array
        result = np.dot(
            filter_response, spectra_arr
        ) / filter_response.sum(axis=1)
        return result.flatten()  # Ensure output is 1D


def load_sensor_filters_csv(filepath, normalise=False):
    """Load sensor filters from a CSV file with comma as separator.

    Args:
        filepath: Path to the CSV file
        normalise: If True, normalize the filter response values

    Returns:
        Dictionary mapping sensor name to a tuple of (wavelengths, filter_matrix)
    """
    import numpy as np
    import pandas as pd
    import os

    try:
        # Read the CSV file
        df = pd.read_csv(filepath, sep=',')

        # Assume first column is wavelength and set as index
        wavelength_column = df.columns[0]
        df.set_index(wavelength_column, inplace=True)

        # Extract wavelengths as numpy array
        wavelengths = np.array(df.index)

        # Extract response functions as numpy array
        response_matrix = df.values.T  # Transpose to get bands as rows

        # Normalize if requested
        if normalise:
            # Normalize each band (row) individually
            row_maxes = response_matrix.max(axis=1, keepdims=True)
            # Avoid division by zero
            row_maxes[row_maxes == 0] = 1.0
            response_matrix = response_matrix / row_maxes

        # Use the file basename as the sensor name (without extension)
        sensor_name = os.path.splitext(os.path.basename(filepath))[0]

        # Return dictionary with sensor name as key
        return {sensor_name: (wavelengths, response_matrix)}

    except Exception as e:
        print(f"Error loading sensor filter from {filepath}: {e}")
        return {}