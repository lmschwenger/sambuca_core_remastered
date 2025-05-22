"""Optimization-based inversion for Sambuca.

This module provides functions for inverting the Sambuca forward model
using optimization techniques from scipy.optimize.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Callable, Any, Union

import numpy as np
from numpy.typing import NDArray
from scipy import optimize

from ..forward_model import forward_model, ForwardModelResults
from .objective_functions import spectral_rmse_with_nedr, distance_f
from .parameters import InversionParameters


@dataclass
class OptimizationResult:
    """Results from the inversion process.

    Attributes:
        parameters: Dictionary of optimized parameter values.
        objective_value: Final value of the objective function.
        observed_spectra: Observed remote sensing reflectance used for inversion.
        modeled_spectra: Modeled remote sensing reflectance from optimized parameters.
        wavelengths: Wavelengths used in the inversion.
        convergence_status: Whether the optimization converged successfully.
        additional_info: Dictionary with additional information about the optimization.
    """
    parameters: Dict[str, float]
    objective_value: float
    observed_spectra: NDArray[np.float64]
    modeled_spectra: NDArray[np.float64]
    wavelengths: NDArray[np.float64]
    convergence_status: bool
    additional_info: Dict[str, Any]
    forward_model_results: ForwardModelResults


def invert_spectrum(
        observed_rrs: NDArray[np.float64],
        inversion_parameters: InversionParameters,
        objective_function: Callable = distance_f,
        initial_values: Optional[List[float]] = None,
        method: str = 'SLSQP',
        options: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
) -> OptimizationResult:
    """Invert a single spectrum to derive water properties.

    Args:
        observed_rrs: Observed remote sensing reflectance.
        inversion_parameters: Parameters for the inversion process.
        objective_function: Function to calculate the error.
        initial_values: Starting values for optimization (defaults to midpoint of bounds).
        method: Optimization method (see scipy.optimize.minimize).
        options: Additional options for the optimizer.

    Returns:
        OptimizationResult with derived parameters and metadata.

    Raises:
        ValueError: If no parameters are specified for inversion.
    """
    # Get parameter bounds
    bounds = inversion_parameters.get_parameter_bounds()
    param_names = inversion_parameters.get_inversion_parameter_names()

    if not bounds:
        raise ValueError("No parameters specified for inversion")

    # Set default initial values to midpoint of bounds if not provided
    if initial_values is None:
        initial_values = inversion_parameters.get_initial_values()

    # Set default options
    if options is None:
        options = {'maxiter': 5000, 'disp': False}

    # Objective function wrapper
    def objective(x):
        # Pass NEDR if available in inversion_parameters
        if hasattr(inversion_parameters, 'nedr') and inversion_parameters.nedr is not None:
            return objective_function(x, observed_rrs, inversion_parameters, nedr=inversion_parameters.nedr)
        else:
            return objective_function(x, observed_rrs, inversion_parameters)

    low_relax = 0.7
    high_relax = 1.3

    cons = None #({'type': 'ineq', 'fun': lambda x: high_relax - (x[4] + x[5] + x[6])},
           # {'type': 'ineq', 'fun': lambda x: (x[4] + x[5] + x[6]) - low_relax})
    objective.observed_rrs = observed_rrs
    # Perform optimization
    result = optimize.minimize(
        objective,
        np.array(initial_values),
        method=method,
        constraints=cons,
        bounds=bounds,
        options=options
    )

    # Get optimized parameters
    optimized_params = result.x
    # Run forward model with optimized parameters to get modeled spectra
    forward_params = inversion_parameters.get_forward_model_params(optimized_params)
    forward_result = forward_model(**forward_params)

    # Create parameter dictionary with names
    param_dict = {name: value for name, value in zip(param_names, optimized_params)}

    # Return results
    return OptimizationResult(
        parameters=param_dict,
        objective_value=result.fun,
        observed_spectra=observed_rrs,
        modeled_spectra=forward_result.rrs,
        wavelengths=inversion_parameters.wavelengths,
        convergence_status=result.success,
        additional_info={
            'iterations': result.nit if hasattr(result, 'nit') else None,
            'message': result.message if hasattr(result, 'message') else None,
            'jacobian': result.jac if hasattr(result, 'jac') else None,
            'hess_inv': result.hess_inv if hasattr(result, 'hess_inv') else None,
            'optimization_result': result,
        },
        forward_model_results=forward_result
    )


def multi_start_inversion(
        observed_rrs: NDArray[np.float64],
        inversion_parameters: InversionParameters,
        objective_function: Callable = distance_f,
        n_starts: int = 5,
        initial_values: Optional[List[float]] = None,
        method: str = 'SLSQP',
        options: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
) -> OptimizationResult:
    """Perform multi-start inversion to avoid local minima.

    This function runs the inversion multiple times with different starting points
    and returns the best result.

    Args:
        observed_rrs: Observed remote sensing reflectance.
        inversion_parameters: Parameters for the inversion process.
        objective_function: Function to calculate the error.
        n_starts: Number of different starting points to try.
        initial_values: Optional starting point to include among the random starts.
        method: Optimization method (see scipy.optimize.minimize).
        options: Additional options for the optimizer.

    Returns:
        OptimizationResult with the best derived parameters.
    """
    # Get parameter bounds
    bounds = inversion_parameters.get_parameter_bounds()

    if not bounds:
        raise ValueError("No parameters specified for inversion")

    best_result = None
    best_error = float('inf')

    # Generate random starting points within bounds
    for _ in range(n_starts):
        # Generate random starting point
        current_initial_values = []
        for lower, upper in bounds:
            current_initial_values.append(lower + np.random.random() * (upper - lower))

        # Run inversion
        result = invert_spectrum(
            observed_rrs,
            inversion_parameters,
            objective_function=objective_function,
            initial_values=current_initial_values,
            method=method,
            options=options
        )

        # Keep track of best result
        if result.objective_value < best_error:
            best_error = result.objective_value
            best_result = result

    # Try with the provided initial values if given
    if initial_values is not None:
        result = invert_spectrum(
            observed_rrs,
            inversion_parameters,
            objective_function=objective_function,
            initial_values=initial_values,
            method=method,
            options=options
        )

        if result.objective_value < best_error:
            best_error = result.objective_value
            best_result = result

    return best_result


def grid_search(
        observed_rrs: NDArray[np.float64],
        inversion_parameters: InversionParameters,
        objective_function: Callable = distance_f,
        grid_size: Union[int, List[int]] = 5,
) -> OptimizationResult:
    """Perform a grid search to find the best parameter set.

    This function evaluates the objective function at a grid of points within
    the parameter bounds and returns the best result.

    Args:
        observed_rrs: Observed remote sensing reflectance.
        inversion_parameters: Parameters for the inversion process.
        objective_function: Function to calculate the error.
        grid_size: Number of points along each parameter dimension.

    Returns:
        OptimizationResult with the best derived parameters.

    Note:
        This approach is only practical for a small number of parameters (1-3).
        For more parameters, use the optimize_from_grid method which uses
        the grid search result as a starting point for further optimization.
    """
    import itertools

    # Get parameter bounds
    bounds = inversion_parameters.get_parameter_bounds()
    param_names = inversion_parameters.get_inversion_parameter_names()

    if not bounds:
        raise ValueError("No parameters specified for inversion")

    # Create parameter grid
    if isinstance(grid_size, int):
        grid_size = [grid_size] * len(bounds)

    param_grids = []
    for i, bound in enumerate(bounds):
        low, high = bound
        param_grids.append(np.linspace(low, high, grid_size[i]))

    # Create all parameter combinations
    param_combinations = list(itertools.product(*param_grids))

    # Evaluate objective function for each parameter combination
    best_error = float('inf')
    best_params = None

    for params in param_combinations:
        # Calculate error
        error = objective_function(params, observed_rrs, inversion_parameters)

        # Keep track of best result
        if error < best_error:
            best_error = error
            best_params = params

    # Get final result by running forward model with best parameters
    forward_params = inversion_parameters.get_forward_model_params(best_params)
    forward_result = forward_model(**forward_params)

    # Create parameter dictionary with names
    param_dict = {name: value for name, value in zip(param_names, best_params)}

    # Return results
    return OptimizationResult(
        parameters=param_dict,
        objective_value=best_error,
        observed_spectra=observed_rrs,
        modeled_spectra=forward_result.rrs,
        wavelengths=inversion_parameters.wavelengths,
        convergence_status=True,
        additional_info={
            'method': 'grid_search',
            'grid_size': grid_size,
        },
        forward_model_results=forward_result
    )


def optimize_from_grid(
        observed_rrs: NDArray[np.float64],
        inversion_parameters: InversionParameters,
        objective_function: Callable = distance_f,
        grid_size: Union[int, List[int]] = 5,
        method: str = 'SLSQP',
        options: Optional[Dict[str, Any]] = None,
) -> OptimizationResult:
    """Perform a grid search followed by local optimization.

    This function first does a grid search to find a good starting point,
    then refines the result using local optimization.

    Args:
        observed_rrs: Observed remote sensing reflectance.
        inversion_parameters: Parameters for the inversion process.
        objective_function: Function to calculate the error.
        grid_size: Number of points along each parameter dimension.
        method: Optimization method for the refinement step.
        options: Additional options for the optimizer.

    Returns:
        OptimizationResult with the best derived parameters.
    """
    # First do a grid search
    grid_result = grid_search(
        observed_rrs,
        inversion_parameters,
        objective_function,
        grid_size
    )

    # Convert parameter dictionary back to list for initial values
    initial_values = [grid_result.parameters[name] for name in inversion_parameters.get_inversion_parameter_names()]

    # Refine with local optimization
    final_result = invert_spectrum(
        observed_rrs,
        inversion_parameters,
        objective_function=objective_function,
        initial_values=initial_values,
        method=method,
        options=options
    )

    # Add grid search info to the result
    final_result.additional_info['grid_search_result'] = grid_result

    return final_result