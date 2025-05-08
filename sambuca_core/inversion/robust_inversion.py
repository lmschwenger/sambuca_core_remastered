"""Robust inversion algorithms for Sambuca that avoid local minima and midpoint issues."""

import copy
import numpy as np
from typing import Dict, List, Optional, Callable, Any, Union, Tuple

from scipy import optimize

from ..forward_model import forward_model
from .optimization import OptimizationResult, invert_spectrum
from .parameters import InversionParameters
from .objective_functions import spectral_rmse, spectral_angle_mapper


def spectral_angle_f_metric(
        params: List[float],
        observed_rrs: np.ndarray,
        inversion_parameters: InversionParameters,
        return_modeled_spectra: bool = False,
        epsilon: float = 1e-9):
    """Calculate combined Spectral Angle + relative magnitude error.

    This combines spectral shape and magnitude differences into one metric.

    Args:
        params: Optimization parameters (values for the parameters being inverted).
        observed_rrs: Observed remote sensing reflectance.
        inversion_parameters: Parameters for the inversion process.
        return_modeled_spectra: If True, return a dictionary with error and modeled spectra.
        epsilon: Small number to avoid division by zero.

    Returns:
        Combined angle-f error metric, or a dictionary with error and modeled spectra.
    """
    # Convert params to forward model inputs
    forward_model_params = inversion_parameters.get_forward_model_params(params)

    # Run forward model
    results = forward_model(**forward_model_params)
    modeled_rrs = results.rrs

    # Calculate spectral angle
    dot_product = np.sum(modeled_rrs * observed_rrs)
    norm_product = np.sqrt(np.sum(modeled_rrs ** 2) * np.sum(observed_rrs ** 2))

    # Avoid division by zero
    if norm_product < epsilon:
        angle = np.pi / 2  # Maximum angle
    else:
        angle = np.arccos(np.clip(dot_product / norm_product, -1.0, 1.0))

    # Calculate f value (normalized RMSE)
    f_val = np.linalg.norm(observed_rrs - modeled_rrs) / (np.sum(observed_rrs) + epsilon)

    # Combined metric
    combined_error = angle * f_val

    if return_modeled_spectra:
        return {
            'error': combined_error,
            'modeled_spectra': modeled_rrs,
            'forward_model_results': results,
            'angle': angle,
            'f_val': f_val
        }

    return combined_error


def scale_parameters(x, bounds):
    """Scale parameters to [0,1] range for better optimization behavior.

    Args:
        x: Original parameters.
        bounds: List of (min, max) tuples.

    Returns:
        Scaled parameters in [0,1] range.
    """
    scaled = []
    for i, val in enumerate(x):
        low, high = bounds[i]
        range_size = high - low
        if range_size < 1e-10:  # Avoid division by zero
            scaled.append(0.5)
        else:
            scaled.append((val - low) / range_size)
    return scaled


def unscale_parameters(scaled_x, bounds):
    """Convert [0,1] scaled parameters back to original range.

    Args:
        scaled_x: Scaled parameters.
        bounds: List of (min, max) tuples.

    Returns:
        Unscaled parameters in original range.
    """
    original = []
    for i, val in enumerate(scaled_x):
        low, high = bounds[i]
        original.append(low + val * (high - low))
    return original


def get_varied_initial_values(inversion_parameters):
    """Generate diverse initial values that aren't at the midpoint.

    Args:
        inversion_parameters: Parameters defining the ranges.

    Returns:
        List of initial values at various positions in the parameter space.
    """
    bounds = inversion_parameters.get_parameter_bounds()
    initial_values = []

    for i, (low, high) in enumerate(bounds):
        # Use 1/3 point instead of midpoint to avoid getting stuck
        initial_values.append(low + (high - low) * 0.33)

    return initial_values


def robust_invert_spectrum(
        observed_rrs: np.ndarray,
        inversion_parameters: InversionParameters,
        use_scaling: bool = True,
        use_spectral_angle_f: bool = True,
        method: str = 'L-BFGS-B',
        n_starts: int = 5,
        options: Optional[Dict[str, Any]] = None) -> OptimizationResult:
    """Robust inversion that avoids getting stuck at parameter midpoints.

    Args:
        observed_rrs: Observed remote sensing reflectance.
        inversion_parameters: Parameters for the inversion process.
        use_scaling: Whether to scale parameters to [0,1] range.
        use_spectral_angle_f: Whether to use the spectral angle * f metric.
        method: Optimization method (see scipy.optimize.minimize).
        n_starts: Number of different starting points to try.
        options: Additional options for the optimizer.

    Returns:
        OptimizationResult with the best derived parameters.
    """
    bounds = inversion_parameters.get_parameter_bounds()
    param_names = inversion_parameters.get_inversion_parameter_names()

    if not bounds:
        raise ValueError("No parameters specified for inversion")

    # Set default options
    if options is None:
        options = {'maxiter': 100, 'disp': False}

    # Choose the objective function
    objective_func = spectral_angle_f_metric if use_spectral_angle_f else spectral_rmse

    # Generate diverse starting points
    initial_points = []

    # Add quarter points and random points
    initial_points.append(get_varied_initial_values(inversion_parameters))

    for _ in range(n_starts - 1):
        # Generate random points within bounds
        random_point = []
        for low, high in bounds:
            # Avoid the exact midpoint by using slightly biased random values
            if np.random.random() < 0.5:
                # Bias towards lower third
                random_point.append(low + np.random.random() * (high - low) * 0.33)
            else:
                # Bias towards upper third
                random_point.append(low + (high - low) * 0.67 + np.random.random() * (high - low) * 0.33)
        initial_points.append(random_point)

    best_result = None
    best_error = float('inf')

    # Try each starting point
    for i, initial_values in enumerate(initial_points):
        try:
            if use_scaling:
                # Scale parameters and bounds
                scaled_bounds = [(0, 1)] * len(bounds)
                scaled_initial = scale_parameters(initial_values, bounds)

                # Define wrapper function for scaled parameters
                def scaled_objective(scaled_x):
                    x = unscale_parameters(scaled_x, bounds)
                    return objective_func(x, observed_rrs, inversion_parameters)

                # Run optimization with scaled parameters
                result = optimize.minimize(
                    scaled_objective,
                    scaled_initial,
                    method=method,
                    bounds=scaled_bounds,
                    options=options
                )

                # Unscale optimized parameters
                optimized_params = unscale_parameters(result.x, bounds)
            else:
                # Use original parameters without scaling
                result = optimize.minimize(
                    lambda x: objective_func(x, observed_rrs, inversion_parameters),
                    initial_values,
                    method=method,
                    bounds=bounds,
                    options=options
                )
                optimized_params = result.x

            # Run forward model with optimized parameters
            forward_params = inversion_parameters.get_forward_model_params(optimized_params)
            forward_result = forward_model(**forward_params)

            # Calculate error with original objective function for consistency
            if use_spectral_angle_f:
                # Get both angle and f components
                result_dict = spectral_angle_f_metric(
                    optimized_params, observed_rrs, inversion_parameters, return_modeled_spectra=True
                )
                final_error = result_dict['error']
                angle = result_dict['angle']
                f_val = result_dict['f_val']
            else:
                final_error = spectral_rmse(optimized_params, observed_rrs, inversion_parameters)
                angle = None
                f_val = None

            # If this is the best result so far, save it
            if final_error < best_error:
                best_error = final_error

                # Create parameter dictionary with names
                param_dict = {
                    name: value for name, value in zip(param_names, optimized_params)
                }

                # Create OptimizationResult
                best_result = OptimizationResult(
                    parameters=param_dict,
                    objective_value=final_error,
                    observed_spectra=observed_rrs,
                    modeled_spectra=forward_result.rrs,
                    wavelengths=inversion_parameters.wavelengths,
                    convergence_status=result.success,
                    additional_info={
                        'start_index': i,
                        'initial_values': initial_values,
                        'iterations': result.nit if hasattr(result, 'nit') else None,
                        'message': result.message if hasattr(result, 'message') else None,
                        'spectral_angle': angle,
                        'f_val': f_val,
                        'scaling_used': use_scaling,
                        'spectral_angle_f_used': use_spectral_angle_f
                    },
                    forward_model_results=forward_result
                )

        except Exception as e:
            print(f"Error with starting point {i}: {e}")
            continue

    # If all optimizations failed, try a simple inversion as fallback
    if best_result is None:
        print("All robust optimizations failed, using standard inversion as fallback")
        return invert_spectrum(observed_rrs, inversion_parameters)

    return best_result


def multi_substrate_inversion(
        observed_rrs: np.ndarray,
        inversion_parameters: InversionParameters,
        substrates: List[np.ndarray],
        objective_function=spectral_rmse,
        method='L-BFGS-B',
        options=None):
    """Try all possible substrate pairs and select the best one.

    Args:
        observed_rrs: Observed remote sensing reflectance.
        inversion_parameters: Parameters for the inversion process.
        substrates: List of substrate spectra to try.
        objective_function: Function to calculate the error.
        method: Optimization method.
        options: Additional options for the optimizer.

    Returns:
        OptimizationResult with the best derived parameters.
    """
    from itertools import combinations

    # Generate all substrate pair combinations
    substrate_combinations = list(combinations(range(len(substrates)), 2))

    best_result = None
    best_error = float('inf')
    best_combo_idx = -1

    # Try each substrate combination
    for combo_idx, (idx1, idx2) in enumerate(substrate_combinations):
        # Create a copy of inversion parameters with this substrate pair
        params_copy = copy.deepcopy(inversion_parameters)
        params_copy.substrate1 = substrates[idx1]
        params_copy.substrate2 = substrates[idx2]

        # Run inversion with these substrates
        try:
            result = robust_invert_spectrum(
                observed_rrs,
                params_copy,
                method=method,
                options=options
            )

            # Keep track of best result
            if result.objective_value < best_error:
                best_error = result.objective_value
                best_result = result
                best_combo_idx = combo_idx

        except Exception as e:
            print(f"Error with substrate combination {idx1}, {idx2}: {e}")
            continue

    if best_result:
        # Add substrate pair info to result
        best_result.additional_info['substrate_pair'] = substrate_combinations[best_combo_idx]

    return best_result