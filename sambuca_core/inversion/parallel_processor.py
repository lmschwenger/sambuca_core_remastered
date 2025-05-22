"""Parallelized optimization and inversion for Sambuca.

This module provides parallelization capabilities for the optimization and inversion
processes in Sambuca, working around Python's multiprocessing pickling limitations.
"""

import multiprocessing as mp
from functools import partial
import numpy as np
from collections import namedtuple
from typing import Callable, Dict, List, Optional, Tuple, Any, Union
from scipy.optimize import minimize as scipy_minimize

# Import at module level to avoid circular imports
from sambuca_core.inversion import OptimizationResult
from sambuca_core.forward_model import forward_model
from .objective_functions import spectral_rmse_with_nedr, distance_f

# Define a named tuple for the minimize results
MinimizeResult = namedtuple('MinimizeResult', ['x', 'nit', 'success', 'fun', 'message'])


# Top-level function for parallelization (must be at module level to be picklable)
def _parallel_minimize_worker(
        args: Tuple,
        method: str = 'L-BFGS-B',
        options: Optional[Dict] = None) -> Any:
    """Worker function for parallelized minimization.

    This must be a top-level function to be picklable with the multiprocessing module.

    Args:
        args: Tuple containing (parameters, observed_rrs, bounds, constraints, objective_function)
        method: Optimization method.
        options: Optimization options.

    Returns:
        Optimization results from scipy.optimize.minimize.
    """
    p0, observed_rrs, bounds, constraints, objective_function = args

    # Create a wrapper around the objective function to handle the observed_rrs
    def objective_wrapper(params):
        return objective_function(params, observed_rrs)

    # Run the optimization
    result = scipy_minimize(
        objective_wrapper,
        p0,
        method=method,
        bounds=bounds,
        constraints=constraints,
        options=options
    )

    return result


def parallel_minimize(
        objective_function: Callable,
        initial_params: List[List[float]],
        observed_rrs: np.ndarray,
        bounds: List[Tuple[float, float]],
        constraints: Optional[List] = None,
        method: str = 'L-BFGS-B',
        options: Optional[Dict] = None,
        n_processes: int = None,
        return_all: bool = False) -> Union[MinimizeResult, List[MinimizeResult]]:
    """Run multiple minimizations in parallel.

    Args:
        objective_function: Function to minimize.
        initial_params: List of initial parameter sets to try.
        observed_rrs: Observed remote sensing reflectance.
        bounds: Bounds for the parameters.
        constraints: Constraints for the optimization.
        method: Optimization method.
        options: Options for the optimizer.
        n_processes: Number of processes to use for parallelization.
        return_all: If True, return all results, otherwise return the best one.

    Returns:
        The best optimization result or all results if return_all is True.
    """
    if options is None:
        options = {'maxiter': 100}

    if constraints is None:
        constraints = []

    # Prepare arguments for parallel processing
    args_list = [(p0, observed_rrs, bounds, constraints, objective_function)
                 for p0 in initial_params]

    # Determine number of processes
    if n_processes is None:
        n_processes = min(mp.cpu_count(), len(initial_params))

    # Create a pool and distribute the work
    with mp.Pool(processes=n_processes) as pool:
        worker_func = partial(_parallel_minimize_worker, method=method, options=options)
        results = pool.map(worker_func, args_list)

    # Process results
    min_results = [
        MinimizeResult(
            x=result.x,
            nit=result.nit if hasattr(result, 'nit') else 0,
            success=result.success,
            fun=result.fun,
            message=result.message if hasattr(result, 'message') else ""
        )
        for result in results
    ]

    if return_all:
        return min_results

    # Find the best result
    valid_results = [r for r in min_results if r.success]

    if not valid_results:
        # If no successful results, return the one with lowest function value
        best_idx = np.argmin([r.fun for r in min_results])
        return min_results[best_idx]

    # Find the best among valid results
    best_idx = np.argmin([r.fun for r in valid_results])
    return valid_results[best_idx]


def parallel_inversion(
        observed_rrs: np.ndarray,
        inversion_parameters,
        n_starts: int = 5,
        n_processes: int = None,
        method: str = 'L-BFGS-B',
        options: Optional[Dict] = None,
        objective_function: Callable = distance_f) -> OptimizationResult:
    """Perform multi-start inversion in parallel.

    Args:
        observed_rrs: Observed remote sensing reflectance.
        inversion_parameters: Parameters for the inversion process.
        n_starts: Number of random starting points.
        n_processes: Number of parallel processes to use.
        method: Optimization method.
        options: Options for the optimizer.
        objective_function: Function to calculate the error.

    Returns:
        Dictionary with the best inversion results.
    """
    # Get parameter bounds
    bounds = inversion_parameters.get_parameter_bounds()
    param_names = inversion_parameters.get_inversion_parameter_names()

    if not bounds:
        raise ValueError("No parameters specified for inversion")

    # Generate random starting points
    initial_params = []

    # Add the midpoint of the bounds as one starting point
    midpoint = [(lower + upper) / 2 for lower, upper in bounds]
    initial_params.append(midpoint)

    # Generate additional random starting points
    for _ in range(n_starts - 1):
        params = []
        for lower, upper in bounds:
            params.append(lower + np.random.random() * (upper - lower))
        initial_params.append(params)

    # Define the objective function specifically for the parallel worker
    def objective_for_worker(params, obs_rrs):
        # Handle NEDR if available
        if hasattr(inversion_parameters, 'nedr') and inversion_parameters.nedr is not None:
            return objective_function(params, obs_rrs, inversion_parameters, nedr=inversion_parameters.nedr)
        else:
            return objective_function(params, obs_rrs, inversion_parameters)
    objective_for_worker(observed_rrs, observed_rrs)  # Pre-bind observed_rrs

    # Run the parallel optimization
    result = parallel_minimize(
        objective_for_worker,
        initial_params,
        observed_rrs,
        bounds,
        method=method,
        options=options if options else {'maxiter': 100},
        n_processes=n_processes
    )

    # Run forward model with optimized parameters to get modeled spectra
    forward_params = inversion_parameters.get_forward_model_params(result.x)
    forward_result = forward_model(**forward_params)

    # Create parameter dictionary with names
    param_dict = {name: value for name, value in zip(param_names, result.x)}

    # Return results
    return OptimizationResult(
        parameters=param_dict,
        objective_value=result.fun,
        observed_spectra=observed_rrs,
        modeled_spectra=forward_result.rrs,
        wavelengths=inversion_parameters.wavelengths,
        convergence_status=result.success,
        additional_info={
            'iterations': result.nit,
            'message': result.message,
            'n_starts': n_starts,
            'method': method,
        },
        forward_model_results=forward_result
    )