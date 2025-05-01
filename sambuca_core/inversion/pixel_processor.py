"""Image pixel processing for Sambuca inversion.

This module provides functions for processing hyperspectral image pixels
to derive water properties using the Sambuca inversion process.
"""

import multiprocessing as mp
from functools import partial
from typing import Dict, List, Tuple, Optional, Any, Union, Callable

import numpy as np
from numpy.typing import NDArray
from tqdm import tqdm

from .optimization import invert_spectrum
from .parameters import InversionParameters
from .lut import LookUpTable


def process_pixel(
        pixel_spectra: NDArray[np.float64],
        inversion_parameters: InversionParameters,
        lut: Optional[LookUpTable] = None,
        refinement: bool = True,
        **kwargs: Any,
) -> Dict[str, Any]:
    """Process a single pixel spectrum.

    Args:
        pixel_spectra: Observed remote sensing reflectance for one pixel.
        inversion_parameters: Parameters for the inversion process.
        lut: Optional look-up table for faster inversion.
        refinement: Whether to refine LUT results with optimization.
        **kwargs: Additional arguments passed to invert_spectrum or lut.invert.

    Returns:
        Dictionary with inverted parameters and metadata.
    """
    # Check for invalid pixel (e.g., negative values or NaNs)
    if np.any(np.isnan(pixel_spectra)) or np.any(pixel_spectra < 0):
        return {
            'parameters': {p: float('nan') for p in inversion_parameters.get_inversion_parameter_names()},
            'error': float('nan'),
            'modeled_spectra': np.full_like(pixel_spectra, float('nan')),
            'convergence': False,
            'status': 'invalid_pixel',
        }

    # Use LUT if provided
    if lut is not None:
        try:
            return lut.invert(pixel_spectra, refine=refinement, **kwargs)
        except Exception as e:
            # Fall back to optimization if LUT fails
            if refinement:
                try:
                    result = invert_spectrum(pixel_spectra, inversion_parameters, **kwargs)
                    return {
                        'parameters': result.parameters,
                        'error': result.objective_value,
                        'modeled_spectra': result.modeled_spectra,
                        'convergence': result.convergence_status,
                        'status': 'optimization_fallback',
                        'error_message': str(e),
                    }
                except Exception as e2:
                    # If both methods fail, return NaN values
                    return {
                        'parameters': {p: float('nan') for p in inversion_parameters.get_inversion_parameter_names()},
                        'error': float('nan'),
                        'modeled_spectra': np.full_like(pixel_spectra, float('nan')),
                        'convergence': False,
                        'status': 'inversion_failed',
                        'error_message': f"LUT: {str(e)}, Optimization: {str(e2)}",
                    }
            else:
                # If LUT fails and no refinement is requested, return NaN values
                return {
                    'parameters': {p: float('nan') for p in inversion_parameters.get_inversion_parameter_names()},
                    'error': float('nan'),
                    'modeled_spectra': np.full_like(pixel_spectra, float('nan')),
                    'convergence': False,
                    'status': 'lut_failed',
                    'error_message': str(e),
                }

    # Otherwise use optimization
    try:
        result = invert_spectrum(pixel_spectra, inversion_parameters, **kwargs)
        return {
            'parameters': result.parameters,
            'error': result.objective_value,
            'modeled_spectra': result.modeled_spectra,
            'convergence': result.convergence_status,
            'status': 'optimization_success',
        }
    except Exception as e:
        # Handle inversion failures
        return {
            'parameters': {p: float('nan') for p in inversion_parameters.get_inversion_parameter_names()},
            'error': float('nan'),
            'modeled_spectra': np.full_like(pixel_spectra, float('nan')),
            'convergence': False,
            'status': 'optimization_failed',
            'error_message': str(e),
        }


def process_image(
        image: NDArray[np.float64],
        inversion_parameters: InversionParameters,
        mask: Optional[NDArray[np.bool_]] = None,
        lut: Optional[LookUpTable] = None,
        n_processes: int = 1,
        progress_bar: bool = True,
        chunk_size: int = 100,
        **kwargs: Any,
) -> Dict[str, NDArray]:
    """Process an entire image to derive water properties.

    Args:
        image: Hyperspectral image with shape (height, width, bands) or (bands, height, width).
        inversion_parameters: Parameters for the inversion process.
        mask: Optional binary mask of valid pixels to process (True = process).
        lut: Optional look-up table for faster inversion.
        n_processes: Number of parallel processes (>1 for parallel processing).
        progress_bar: Whether to show a progress bar.
        chunk_size: Number of pixels to process in each batch (for parallel processing).
        **kwargs: Additional arguments passed to process_pixel.

    Returns:
        Dictionary mapping parameter names to image arrays.

    Raises:
        ValueError: If the image dimensions are invalid.
    """
    # Check image dimensions
    if len(image.shape) != 3:
        raise ValueError(f"Image must have 3 dimensions, got {len(image.shape)}")

    # Handle different band dimension orders
    if image.shape[0] == len(inversion_parameters.wavelengths):
        # Bands first format (bands, height, width)
        bands, height, width = image.shape
        # Transpose to (height, width, bands) for easier pixel access
        image = np.transpose(image, (1, 2, 0))
    elif image.shape[2] == len(inversion_parameters.wavelengths):
        # Bands last format (height, width, bands)
        height, width, bands = image.shape
    else:
        raise ValueError(
            f"Image band dimension ({image.shape}) does not match wavelengths length "
            f"({len(inversion_parameters.wavelengths)})"
        )

    # Create mask if not provided
    if mask is None:
        mask = np.ones((height, width), dtype=bool)
    elif mask.shape != (height, width):
        raise ValueError(f"Mask shape {mask.shape} does not match image shape ({height}, {width})")

    # Get masked pixel coordinates
    y_indices, x_indices = np.where(mask)
    n_pixels = len(y_indices)

    if n_pixels == 0:
        raise ValueError("No pixels to process (empty mask)")

    # Get parameter names
    param_names = inversion_parameters.get_inversion_parameter_names()

    # Function to process a batch of masked pixels
    def process_pixel_batch(batch_indices):
        results = []
        for idx in batch_indices:
            y, x = y_indices[idx], x_indices[idx]
            pixel_spectra = image[y, x, :]
            results.append((idx, process_pixel(pixel_spectra, inversion_parameters, lut, **kwargs)))
        return results

    # Process pixels
    all_results = []

    if n_processes > 1:
        # Parallel processing in batches
        batch_indices = [list(range(i, min(i + chunk_size, n_pixels)))
                         for i in range(0, n_pixels, chunk_size)]

        with mp.Pool(processes=n_processes) as pool:
            if progress_bar:
                batch_results = list(tqdm(
                    pool.imap(process_pixel_batch, batch_indices),
                    total=len(batch_indices),
                    desc="Processing pixel batches"
                ))
            else:
                batch_results = list(pool.imap(process_pixel_batch, batch_indices))

            # Flatten batch results
            for batch in batch_results:
                all_results.extend(batch)
    else:
        # Sequential processing
        iterator = range(n_pixels)
        if progress_bar:
            iterator = tqdm(iterator, desc="Processing pixels")

        for idx in iterator:
            y, x = y_indices[idx], x_indices[idx]
            pixel_spectra = image[y, x, :]
            all_results.append((idx, process_pixel(pixel_spectra, inversion_parameters, lut, **kwargs)))

    # Sort results by original index
    all_results.sort(key=lambda x: x[0])

    # Initialize output arrays
    output = {}
    for param in param_names:
        output[param] = np.full((height, width), np.nan)

    output['error'] = np.full((height, width), np.nan)
    output['convergence'] = np.full((height, width), False)
    output['status'] = np.full((height, width), '', dtype=object)

    # Fill output arrays
    for idx, result in all_results:
        y, x = y_indices[idx], x_indices[idx]

        for param, value in result['parameters'].items():
            output[param][y, x] = value

        output['error'][y, x] = result.get('error', np.nan)
        output['convergence'][y, x] = result.get('convergence', False)
        output['status'][y, x] = result.get('status', 'unknown')

    return output


def batch_process_image(
        image: NDArray[np.float64],
        inversion_parameters: InversionParameters,
        batch_size: Tuple[int, int] = (100, 100),
        overlap: int = 0,
        **kwargs: Any,
) -> Dict[str, NDArray]:
    """Process a large image in spatial batches to manage memory usage.

    Args:
        image: Hyperspectral image with shape (height, width, bands) or (bands, height, width).
        inversion_parameters: Parameters for the inversion process.
        batch_size: Size of spatial batches (height, width).
        overlap: Number of pixels to overlap between batches (helps reduce edge artifacts).
        **kwargs: Additional arguments passed to process_image.

    Returns:
        Dictionary mapping parameter names to image arrays.
    """
    # Handle different band dimension orders
    if image.shape[0] == len(inversion_parameters.wavelengths):
        # Bands first format (bands, height, width)
        bands, height, width = image.shape
        # Transpose to (height, width, bands) for easier pixel access
        image = np.transpose(image, (1, 2, 0))
    elif image.shape[2] == len(inversion_parameters.wavelengths):
        # Bands last format (height, width, bands)
        height, width, bands = image.shape
    else:
        raise ValueError(
            f"Image band dimension ({image.shape}) does not match wavelengths length "
            f"({len(inversion_parameters.wavelengths)})"
        )

    # Get parameter names
    param_names = inversion_parameters.get_inversion_parameter_names()

    # Initialize output arrays
    output = {}
    for param in param_names:
        output[param] = np.full((height, width), np.nan)

    output['error'] = np.full((height, width), np.nan)
    output['convergence'] = np.full((height, width), False)
    output['status'] = np.full((height, width), '', dtype=object)

    # Calculate batch coordinates
    batch_height, batch_width = batch_size

    y_starts = list(range(0, height, batch_height - overlap))
    x_starts = list(range(0, width, batch_width - overlap))

    # Ensure we don't go beyond image boundaries
    y_starts = [min(y, height - batch_height) for y in y_starts if y < height]
    x_starts = [min(x, width - batch_width) for x in x_starts if x < width]

    # Add final batch if needed
    if y_starts[-1] + batch_height < height:
        y_starts.append(height - batch_height)
    if x_starts[-1] + batch_width < width:
        x_starts.append(width - batch_width)

    total_batches = len(y_starts) * len(x_starts)
    batch_count = 0

    # Process batches
    progress_bar = kwargs.pop('progress_bar', True)

    for y_start in y_starts:
        for x_start in x_starts:
            batch_count += 1
            if progress_bar:
                print(f"Processing batch {batch_count}/{total_batches} at ({y_start}, {x_start})")

            # Extract batch
            y_end = min(y_start + batch_height, height)
            x_end = min(x_start + batch_width, width)

            batch = image[y_start:y_end, x_start:x_end, :]

            # Process batch
            batch_results = process_image(batch, inversion_parameters, **kwargs)

            # If it's not an overlapping region or overlapping with higher priority,
            # copy results to output
            for param_name, param_array in batch_results.items():
                output[param_name][y_start:y_end, x_start:x_end] = param_array
            valid_depths = output["depth"][~np.isnan(output["depth"])]
            print(f"Depth statistics:")
            print(f"  Min depth: {np.min(valid_depths):.2f} m")
            print(f"  Max depth: {np.max(valid_depths):.2f} m")
            print(f"  Mean depth: {np.mean(valid_depths):.2f} m")
            print(f"  Median depth: {np.median(valid_depths):.2f} m")
    return output