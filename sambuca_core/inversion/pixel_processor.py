"""Image pixel processing for Sambuca inversion with optimized performance.

This module provides functions for processing hyperspectral image pixels
to derive water properties using the Sambuca inversion process, with
optimizations for performance especially on Windows systems.
"""

import os
import multiprocessing as mp
from functools import partial
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
import concurrent.futures
import numpy as np
from numpy.typing import NDArray
from tqdm import tqdm
import time

from .optimization import invert_spectrum, multi_start_inversion
from .parameters import InversionParameters
from .lut import LookUpTable

from ..forward_model import forward_model
from .optimization import invert_spectrum, multi_start_inversion
from .parameters import InversionParameters
from .lut import LookUpTable
from .scipy_objective import SciPyObjective  # Add this import
from .objective_functions import distance_f  # Add this import


def process_pixel(
        pixel_spectra: NDArray[np.float64],
        inversion_parameters: InversionParameters,
        lut: Optional[LookUpTable] = None,
        refinement: bool = True,
        use_multi_start: bool = False,
        n_starts: int = 5,
        sensor_filter=None,  # Add this parameter
        **kwargs: Any,
) -> Dict[str, Any]:
    """Process a single pixel spectrum.

    Args:
        pixel_spectra: Observed remote sensing reflectance for one pixel.
        inversion_parameters: Parameters for the inversion process.
        lut: Optional look-up table for faster inversion.
        refinement: Whether to refine LUT results with optimization.
        use_multi_start: Whether to use multi-start inversion.
        n_starts: Number of starting points for multi-start inversion.
        sensor_filter: Sensor filter for the SciPyObjective.
        **kwargs: Additional arguments passed to invert_spectrum or lut.invert.

    Returns:
        Dictionary with inverted parameters and metadata.
    """
    # Check for invalid pixel
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
            if hasattr(inversion_parameters, 'nedr') and inversion_parameters.nedr is not None:
                kwargs['nedr'] = inversion_parameters.nedr

            lut_result = lut.invert(pixel_spectra, refine=refinement, **kwargs)

            # If using multi-start refinement after LUT
            if refinement and use_multi_start:
                # Use LUT result as one of the starting points
                lut_params = [lut_result['parameters'][p] for p in inversion_parameters.get_inversion_parameter_names()]

                # Create SciPyObjective for multi-start
                nedr_values = inversion_parameters.nedr if hasattr(inversion_parameters, 'nedr') else None
                objective = SciPyObjective(
                    sensor_filter=sensor_filter,
                    fixed_parameters=inversion_parameters,
                    error_function=distance_f,
                    nedr=nedr_values
                )
                objective._observed_rrs = pixel_spectra

                # Perform multi-start optimization using SciPyObjective
                result = multi_start_with_objective(
                    objective,
                    inversion_parameters,
                    n_starts=n_starts,
                    initial_values=lut_params,
                    **kwargs
                )

                return {
                    'parameters': result['parameters'],
                    'error': result['error'],
                    'modeled_spectra': result['modeled_spectra'],
                    'convergence': result['convergence'],
                    'status': 'multi_start_after_lut',
                    'lut_result': lut_result  # Keep LUT result for comparison
                }
            else:
                return lut_result

        except Exception as e:
            # Fall back to optimization if LUT fails
            pass

    # Use multi-start or regular optimization with SciPyObjective
    try:
        # Ensure sensor_filter is provided
        if sensor_filter is None:
            raise ValueError("sensor_filter must be provided for inversion")

        # Create a SciPyObjective instance
        nedr_values = inversion_parameters.nedr if hasattr(inversion_parameters, 'nedr') else None
        objective = SciPyObjective(
            sensor_filter=sensor_filter,
            fixed_parameters=inversion_parameters,
            error_function=distance_f,
            nedr=nedr_values
        )

        # Set the observed rrs for this pixel
        objective._observed_rrs = pixel_spectra

        # Get the parameter bounds
        bounds = inversion_parameters.get_parameter_bounds()
        param_names = inversion_parameters.get_inversion_parameter_names()

        # Get initial values
        initial_values = kwargs.get('initial_values', inversion_parameters.get_initial_values())

        # Set up constraints (similar to SWAMpy)
        low_relax = kwargs.get('low_relax', 0.7)
        high_relax = kwargs.get('high_relax', 1.3)
        substrate_indices = kwargs.get('substrate_indices', [4, 5, 6])  # Default as in SWAMpy

        cons = [
            {'type': 'ineq', 'fun': lambda x: high_relax - sum(x[i] for i in substrate_indices if i < len(x))},
            {'type': 'ineq', 'fun': lambda x: sum(x[i] for i in substrate_indices if i < len(x)) - low_relax}
        ]

        # Get optimization method and options
        method = kwargs.get('method', 'SLSQP')
        options = kwargs.get('options', {'disp': False, 'maxiter': 5000})

        if use_multi_start:
            # Perform multi-start optimization
            result = multi_start_with_objective(
                objective,
                inversion_parameters,
                n_starts=n_starts,
                method=method,
                constraints=cons,
                options=options,
                **kwargs
            )

            return result
        else:
            # Run single optimization
            from scipy import optimize
            opt_result = optimize.minimize(
                objective,
                initial_values,
                method=method,
                bounds=bounds,
                constraints=cons,
                options=options
            )

            # Run forward model to get modeled spectra
            forward_params = inversion_parameters.get_forward_model_params(opt_result.x)
            forward_result = forward_model(**forward_params)

            # Create parameter dictionary
            param_dict = {name: value for name, value in zip(param_names, opt_result.x)}

            return {
                'parameters': param_dict,
                'error': opt_result.fun,
                'modeled_spectra': forward_result.rrs,
                'convergence': opt_result.success,
                'status': 'optimization_success',
                'iterations': opt_result.nit,
                'message': opt_result.message,
            }
    except Exception as e:
        # Handle inversion failures
        return {
            'parameters': {p: float('nan') for p in inversion_parameters.get_inversion_parameter_names()},
            'error': float('nan'),
            'modeled_spectra': np.full_like(pixel_spectra, float('nan')),
            'convergence': False,
            'status': f"{'multi_start' if use_multi_start else 'optimization'}_failed",
            'error_message': str(e),
        }


# Helper function for multi-start optimization with SciPyObjective
def multi_start_with_objective(
        objective: 'SciPyObjective',
        inversion_parameters: InversionParameters,
        n_starts: int = 5,
        initial_values: Optional[List[float]] = None,
        method: str = 'SLSQP',
        constraints=None,
        options: Optional[Dict[str, Any]] = None,
        **kwargs: Any
) -> Dict[str, Any]:
    """Perform multi-start optimization using SciPyObjective.

    Args:
        objective: The SciPyObjective instance.
        inversion_parameters: Parameters for the inversion process.
        n_starts: Number of random starting points.
        initial_values: Optional specific initial values to include.
        method: Optimization method.
        constraints: Optimization constraints.
        options: Optimization options.
        **kwargs: Additional arguments.

    Returns:
        Dictionary with best optimization result.
    """
    from scipy import optimize

    # Get parameter bounds
    bounds = inversion_parameters.get_parameter_bounds()
    param_names = inversion_parameters.get_inversion_parameter_names()

    # Default options if not provided
    if options is None:
        options = {'disp': False, 'maxiter': 5000}

    best_result = None
    best_error = float('inf')

    # Try with multiple starting points
    for _ in range(n_starts):
        # Generate random starting point within bounds
        random_start = []
        for lower, upper in bounds:
            random_start.append(lower + np.random.random() * (upper - lower))

        # Run optimization
        result = optimize.minimize(
            objective,
            random_start,
            method=method,
            bounds=bounds,
            constraints=constraints,
            options=options
        )

        # Keep track of best result
        if result.fun < best_error and result.success:
            best_error = result.fun
            best_result = result

    # Try with the provided initial values if given
    if initial_values is not None:
        result = optimize.minimize(
            objective,
            initial_values,
            method=method,
            bounds=bounds,
            constraints=constraints,
            options=options
        )

        if result.fun < best_error and result.success:
            best_error = result.fun
            best_result = result

    # If no successful optimization, return the best we have
    if best_result is None:
        # Try to get any result, even if not successful
        for _ in range(1):
            random_start = []
            for lower, upper in bounds:
                random_start.append(lower + np.random.random() * (upper - lower))

            result = optimize.minimize(
                objective,
                random_start,
                method=method,
                bounds=bounds,
                constraints=constraints,
                options=options
            )

            if result.fun < best_error:
                best_error = result.fun
                best_result = result

        if best_result is None:
            raise ValueError("All optimization attempts failed")

    # Run forward model to get modeled spectra
    forward_params = inversion_parameters.get_forward_model_params(best_result.x)
    forward_result = forward_model(**forward_params)

    # Create parameter dictionary
    param_dict = {name: value for name, value in zip(param_names, best_result.x)}

    return {
        'parameters': param_dict,
        'error': best_result.fun,
        'modeled_spectra': forward_result.rrs,
        'convergence': best_result.success,
        'status': 'multi_start_success',
        'iterations': best_result.nit,
        'message': best_result.message,
    }

# Function to process a batch of pixels (used by both ThreadPoolExecutor and ProcessPoolExecutor)
def _process_pixel_batch(batch_data):
    """Process a batch of pixels.

    Args:
        batch_data: Tuple containing (pixel_indices, pixel_coords, image_data,
                    inversion_parameters, lut, kwargs)

    Returns:
        List of (index, result) tuples
    """
    pixel_indices, pixel_coords, image_data, inversion_parameters, lut, kwargs = batch_data
    results = []

    # Extract sensor_filter
    sensor_filter = kwargs.get('sensor_filter', None)

    # Ensure sensor_filter is provided
    if sensor_filter is None:
        raise ValueError("sensor_filter must be provided for inversion")

    for i, idx in enumerate(pixel_indices):
        print(f"{i} / {len(pixel_indices)}")
        y, x = pixel_coords[i]
        pixel_spectra = image_data[y, x, :]
        results.append((idx, process_pixel(
            pixel_spectra,
            inversion_parameters,
            lut,
            **kwargs
        )))

    return results


def process_image(
        image: NDArray[np.float64],
        inversion_parameters: InversionParameters,
        mask: Optional[NDArray[np.bool_]] = None,
        lut: Optional[LookUpTable] = None,
        n_processes: int = None,
        progress_bar: bool = True,
        chunk_size: int = 500,
        use_threads: bool = True,
        use_multi_start: bool = False,
        n_starts: int = 5,
        sensor_filter=None,  # Add this parameter
        **kwargs: Any,
) -> Dict[str, NDArray]:
    """Process an entire image to derive water properties with optimized performance.

    Args:
        image: Hyperspectral image with shape (height, width, bands) or (bands, height, width).
        inversion_parameters: Parameters for the inversion process.
        mask: Optional binary mask of valid pixels to process (True = process).
        lut: Optional look-up table for faster inversion.
        n_processes: Number of parallel processes/threads. Default is None (uses CPU count).
        progress_bar: Whether to show a progress bar.
        chunk_size: Number of pixels to process in each batch.
        use_threads: If True, use ThreadPoolExecutor instead of ProcessPoolExecutor.
        use_multi_start: Whether to use multi-start inversion.
        n_starts: Number of starting points for multi-start inversion.
        sensor_filter: Sensor filter needed for SciPyObjective.
        **kwargs: Additional arguments passed to process_pixel.

    Returns:
        Dictionary mapping parameter names to image arrays.
    """
    # Update the kwargs with the new parameters
    kwargs.update({
        'use_multi_start': use_multi_start,
        'n_starts': n_starts,
        'sensor_filter': sensor_filter
    })

    start_time = time.time()

    # Ensure sensor_filter is provided
    if sensor_filter is None:
        raise ValueError("sensor_filter must be provided for inversion")

    # Default n_processes to CPU count if not specified
    if n_processes is None:
        n_processes = max(1, os.cpu_count() - 1)  # Leave one CPU free

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

    print(f"Processing {n_pixels} pixels from image of shape {image.shape}")

    # Get parameter names
    param_names = inversion_parameters.get_inversion_parameter_names()

    # Prepare pixel batches for parallel processing
    pixel_indices = list(range(n_pixels))
    pixel_coords = list(zip(y_indices, x_indices))

    # Create batches of pixels for processing
    batch_indices = [list(range(i, min(i + chunk_size, n_pixels)))
                     for i in range(0, n_pixels, chunk_size)]

    all_results = []

    # Create lists of batched data to avoid pickling issues on Windows
    batched_data = []
    for indices in batch_indices:
        coords = [pixel_coords[i] for i in indices]
        batch = (indices, coords, image, inversion_parameters, lut, kwargs)
        batched_data.append(batch)

    # Process pixels in parallel
    executor_class = concurrent.futures.ThreadPoolExecutor if use_threads else concurrent.futures.ProcessPoolExecutor

    with executor_class(max_workers=n_processes) as executor:
        # Submit all batches
        if progress_bar:
            futures = list(tqdm(
                executor.map(_process_pixel_batch, batched_data),
                total=len(batched_data),
                desc=f"Processing pixel batches ({'threads' if use_threads else 'processes'})"
            ))
        else:
            futures = list(executor.map(_process_pixel_batch, batched_data))

        # Collect results
        for batch_results in futures:
            all_results.extend(batch_results)

    # Sort results by original index
    all_results.sort(key=lambda x: x[0])

    # Initialize output arrays
    output = {}
    for param in param_names:
        output[param] = np.full((height, width), np.nan)

    output['error'] = np.full((height, width), np.nan)
    output['convergence'] = np.full((height, width), False)
    output['status'] = np.full((height, width), '', dtype=object)

    # Add modeled spectra array if needed for visualization
    output['modeled_spectra'] = np.full((height, width, bands), np.nan)

    # Fill output arrays
    for idx, result in all_results:
        y, x = y_indices[idx], x_indices[idx]

        for param, value in result['parameters'].items():
            output[param][y, x] = value

        output['error'][y, x] = result.get('error', np.nan)
        output['convergence'][y, x] = result.get('convergence', False)
        output['status'][y, x] = result.get('status', 'unknown')

        # Add modeled spectra if available
        if 'modeled_spectra' in result:
            output['modeled_spectra'][y, x, :] = result['modeled_spectra']

    elapsed_time = time.time() - start_time
    print(f"Image processing completed in {elapsed_time:.2f} seconds")

    # Calculate statistics on processed pixels if depth is present
    if 'depth' in output:
        valid_mask = ~np.isnan(output['depth'])
        valid_depths = output['depth'][valid_mask]
        if len(valid_depths) > 0:
            print(f"Depth statistics:")
            print(f"  Valid pixels: {len(valid_depths)} of {n_pixels} ({len(valid_depths)/n_pixels*100:.1f}%)")
            print(f"  Min depth: {np.min(valid_depths):.2f} m")
            print(f"  Max depth: {np.max(valid_depths):.2f} m")
            print(f"  Mean depth: {np.mean(valid_depths):.2f} m")
            print(f"  Median depth: {np.median(valid_depths):.2f} m")

    return output


def batch_process_image(
        image: NDArray[np.float64],
        inversion_parameters: InversionParameters,
        batch_size: Tuple[int, int] = (256, 256),
        overlap: int = 0,
        n_processes: int = None,
        use_threads: bool = True,
        save_intermediates: bool = False,
        output_dir: str = None,
        **kwargs: Any,
) -> Dict[str, NDArray]:
    """Process a large image in spatial batches with improved memory management.

    Args:
        image: Hyperspectral image with shape (height, width, bands) or (bands, height, width).
        inversion_parameters: Parameters for the inversion process.
        batch_size: Size of spatial batches (height, width).
        overlap: Number of pixels to overlap between batches (helps reduce edge artifacts).
        n_processes: Number of parallel processes/threads per batch.
        use_threads: Whether to use threads instead of processes (better for Windows).
        save_intermediates: Whether to save intermediate results to disk to reduce memory usage.
        output_dir: Directory to save intermediate results if save_intermediates is True.
        **kwargs: Additional arguments passed to process_image.

    Returns:
        Dictionary mapping parameter names to image arrays.
    """
    import os
    import tempfile
    import shutil

    start_time = time.time()

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

    # Add modeled spectra array if needed for visualization
    output['modeled_spectra'] = np.full((height, width, bands), np.nan)

    # Calculate batch coordinates with smarter batching - prioritize square batches
    batch_height, batch_width = batch_size

    # Use temporary directory for intermediate results if saving
    temp_dir = None
    if save_intermediates:
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            temp_dir = output_dir
        else:
            temp_dir = tempfile.mkdtemp(prefix="sambuca_batch_")

    try:
        # Calculate batch boundaries
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

        # Process batches
        progress_bar = kwargs.pop('progress_bar', True)
        batch_count = 0

        if progress_bar:
            batch_iterator = tqdm(
                [(y, x) for y in y_starts for x in x_starts],
                total=total_batches,
                desc=f"Processing {total_batches} image batches"
            )
        else:
            batch_iterator = [(y, x) for y in y_starts for x in x_starts]

        for y_start, x_start in batch_iterator:
            batch_count += 1

            # Extract batch
            y_end = min(y_start + batch_height, height)
            x_end = min(x_start + batch_width, width)

            batch = image[y_start:y_end, x_start:x_end, :]

            # Process batch
            batch_results = process_image(
                batch,
                inversion_parameters,
                n_processes=n_processes,
                use_threads=use_threads,
                progress_bar=False,  # Avoid nested progress bars
                **kwargs
            )

            # If saving intermediates, save to disk and clear from memory
            if save_intermediates and temp_dir:
                batch_file = os.path.join(temp_dir, f"batch_{y_start}_{x_start}.npz")
                np.savez_compressed(batch_file, **batch_results)

                # If we're just saving intermediates and not keeping in memory, continue
                if not kwargs.get('keep_intermediates_in_memory', False):
                    continue

            # Copy results to output
            for param_name, param_array in batch_results.items():
                output[param_name][y_start:y_end, x_start:x_end] = param_array

            # Report progress on valid depths if available
            if 'depth' in output and batch_count % 5 == 0:
                valid_mask = ~np.isnan(output['depth'])
                valid_pixels = np.sum(valid_mask)
                if valid_pixels > 0:
                    valid_depths = output['depth'][valid_mask]
                    print(f"Progress after {batch_count}/{total_batches} batches:")
                    print(f"  Valid pixels: {valid_pixels} ({valid_pixels/(height*width)*100:.1f}%)")
                    print(f"  Depth range: {np.min(valid_depths):.2f} - {np.max(valid_depths):.2f} m")
                    print(f"  Mean depth: {np.mean(valid_depths):.2f} m")

        # If we saved intermediates, load and combine them
        if save_intermediates and temp_dir and not kwargs.get('keep_intermediates_in_memory', False):
            print("Combining intermediate results...")
            for y_start, x_start in batch_iterator:
                y_end = min(y_start + batch_height, height)
                x_end = min(x_start + batch_width, width)

                batch_file = os.path.join(temp_dir, f"batch_{y_start}_{x_start}.npz")
                if os.path.exists(batch_file):
                    batch_data = np.load(batch_file)
                    for param_name in output.keys():
                        if param_name in batch_data:
                            output[param_name][y_start:y_end, x_start:x_end] = batch_data[param_name]

        # Calculate final statistics on processed results
        if 'depth' in output:
            valid_mask = ~np.isnan(output['depth'])
            valid_depths = output['depth'][valid_mask]
            if len(valid_depths) > 0:
                print("\nFinal depth statistics:")
                print(f"  Valid pixels: {np.sum(valid_mask)} of {height*width} ({np.sum(valid_mask)/(height*width)*100:.1f}%)")
                print(f"  Min depth: {np.min(valid_depths):.2f} m")
                print(f"  Max depth: {np.max(valid_depths):.2f} m")
                print(f"  Mean depth: {np.mean(valid_depths):.2f} m")
                print(f"  Median depth: {np.median(valid_depths):.2f} m")

        elapsed_time = time.time() - start_time
        print(f"Total batch processing completed in {elapsed_time:.2f} seconds")

        return output

    finally:
        # Clean up temp directory if we created one and don't need to keep it
        if save_intermediates and temp_dir and not output_dir and not kwargs.get('keep_intermediate_files', False):
            shutil.rmtree(temp_dir)
