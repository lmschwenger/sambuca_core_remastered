"""Look-up table based inversion for Sambuca.

This module provides a LUT-based approach for fast inversion of the Sambuca
forward model. This approach is especially useful for processing large images
where optimization-based inversion would be too computationally expensive.
"""

import os
import pickle
import itertools
from typing import Dict, List, Tuple, Union, Optional, Any

import numpy as np
from numpy.typing import NDArray
from tqdm import tqdm

from ..forward_model import forward_model
from .parameters import InversionParameters
from .optimization import invert_spectrum


class LookUpTable:
    """Look-up table for rapid inversion of Sambuca parameters.

    This class builds and stores a look-up table of pre-computed spectra for
    different parameter combinations, enabling fast inversion by finding the
    closest match to an observed spectrum.
    """

    def __init__(self, inversion_parameters: InversionParameters):
        """Initialize the look-up table with parameter ranges.

        Args:
            inversion_parameters: Parameters defining the ranges for LUT generation.
        """
        self.inversion_parameters = inversion_parameters
        self.param_names = inversion_parameters.get_inversion_parameter_names()
        self.bounds = inversion_parameters.get_parameter_bounds()
        self.points = {}  # Dict mapping parameter tuples to spectra
        self.table_built = False
        self.grid_shape = None  # Shape of the parameter grid
        self.param_values = []  # List of parameter values for each dimension

    def build_table(
            self,
            grid_size: Union[int, List[int]] = 10,
            progress_bar: bool = True,
    ) -> None:
        """Build the look-up table by running the forward model for parameter combinations.

        Args:
            grid_size: Number of points along each parameter dimension (can be int or list).
            progress_bar: Whether to show a progress bar.

        Raises:
            ValueError: If no parameters are specified for inversion.
        """
        # Check if we have parameters to invert
        if not self.bounds:
            raise ValueError("No parameters specified for inversion")

        # Create parameter grid
        if isinstance(grid_size, int):
            grid_size = [grid_size] * len(self.bounds)

        self.param_values = []
        for i, bound in enumerate(self.bounds):
            low, high = bound
            self.param_values.append(np.linspace(low, high, grid_size[i]))

        self.grid_shape = tuple(len(values) for values in self.param_values)

        # Create all parameter combinations
        param_combinations = list(itertools.product(*self.param_values))
        total_combinations = len(param_combinations)

        if progress_bar:
            param_combinations = tqdm(param_combinations, total=total_combinations,
                                      desc="Building LUT")

        # Calculate spectra for each parameter combination
        for params in param_combinations:
            # Run forward model
            fwd_params = self.inversion_parameters.get_forward_model_params(list(params))
            results = forward_model(**fwd_params)

            # Store results
            self.points[params] = results.rrs

        self.table_built = True
        print(f"Look-up table built with {total_combinations} parameter combinations")

    def save(self, filename: str) -> None:
        """Save the look-up table to a file.

        Args:
            filename: Path to save the LUT.
        """
        data_to_save = {
            'inversion_parameters': self.inversion_parameters,
            'param_names': self.param_names,
            'bounds': self.bounds,
            'points': self.points,
            'table_built': self.table_built,
            'grid_shape': self.grid_shape,
            'param_values': self.param_values,
        }

        with open(filename, 'wb') as f:
            pickle.dump(data_to_save, f)

        print(f"Look-up table saved to {filename}")

    @classmethod
    def load(cls, filename: str) -> 'LookUpTable':
        """Load a look-up table from a file.

        Args:
            filename: Path to the saved LUT file.

        Returns:
            Loaded LookUpTable object.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Look-up table file {filename} not found")

        with open(filename, 'rb') as f:
            data = pickle.load(f)

        lut = cls(data['inversion_parameters'])
        lut.param_names = data['param_names']
        lut.bounds = data['bounds']
        lut.points = data['points']
        lut.table_built = data['table_built']
        lut.grid_shape = data['grid_shape']
        lut.param_values = data['param_values']

        return lut

    def invert(
            self,
            observed_rrs: NDArray[np.float64],
            metric: str = 'rmse',
            refine: bool = True,
            n_best: int = 1,
    ) -> Dict[str, Any]:
        """Invert observed reflectance using the look-up table.

        Args:
            observed_rrs: Observed remote sensing reflectance.
            metric: Error metric ('rmse' or 'sam' [Spectral Angle Mapper]).
            refine: Whether to refine the result with local optimization.
            n_best: Number of best matches to consider for refinement.

        Returns:
            Dictionary with inverted parameters and metadata.

        Raises:
            ValueError: If the look-up table has not been built yet or if
                an unknown metric is specified.
        """
        if not self.table_built:
            raise ValueError("Look-up table not built yet, call build_table() first")

        # Find closest matches in the LUT
        errors = []
        params_list = []
        spectra_list = []

        for params, spectra in self.points.items():
            if metric == 'rmse':
                error = np.sqrt(np.mean((spectra - observed_rrs) ** 2))
            elif metric == 'sam':
                dot_product = np.sum(spectra * observed_rrs)
                norm_product = np.sqrt(np.sum(spectra ** 2) * np.sum(observed_rrs ** 2))
                if norm_product < 1e-10:
                    error = np.pi / 2
                else:
                    error = np.arccos(np.clip(dot_product / norm_product, -1.0, 1.0))
            else:
                raise ValueError(f"Unknown metric: {metric}")

            errors.append(error)
            params_list.append(params)
            spectra_list.append(spectra)

        # Sort by error
        sorted_indices = np.argsort(errors)
        best_indices = sorted_indices[:n_best]

        best_errors = [errors[i] for i in best_indices]
        best_params = [params_list[i] for i in best_indices]
        best_spectra = [spectra_list[i] for i in best_indices]

        # Optional refinement using optimization
        if refine:
            # Use the best LUT match as initial values
            initial_values = list(best_params[0])

            # Run optimization
            result = invert_spectrum(
                observed_rrs,
                self.inversion_parameters,
                initial_values=initial_values,
                method='L-BFGS-B',
                options={'maxiter': 50}
            )

            # Convert best LUT parameters to dictionary
            lut_params_dict = {}
            for i, param_name in enumerate(self.param_names):
                lut_params_dict[param_name] = best_params[0][i]

            # Return optimization results
            return {
                'parameters': result.parameters,
                'error': result.objective_value,
                'modeled_spectra': result.modeled_spectra,
                'lut_parameters': lut_params_dict,
                'lut_error': best_errors[0],
                'lut_spectra': best_spectra[0],
                'forward_model_results': result.forward_model_results,
            }

        # Return best LUT result
        best_params_dict = {}
        for i, param_name in enumerate(self.param_names):
            best_params_dict[param_name] = best_params[0][i]

        return {
            'parameters': best_params_dict,
            'error': best_errors[0],
            'modeled_spectra': best_spectra[0],
            'all_best_params': best_params[:n_best],
            'all_best_errors': best_errors[:n_best],
        }

    def get_spectra_cube(self) -> Tuple[NDArray[np.float64], List[NDArray[np.float64]]]:
        """Get the pre-computed spectra as a parameter cube.

        This function organizes the pre-computed spectra into a multi-dimensional
        array (cube) corresponding to the parameter grid.

        Returns:
            Tuple containing:
                - Multi-dimensional array of spectra
                - List of parameter value arrays for each dimension

        Raises:
            ValueError: If the look-up table has not been built yet.
        """
        if not self.table_built:
            raise ValueError("Look-up table not built yet, call build_table() first")

        # Get number of wavelengths from any entry
        first_spectra = next(iter(self.points.values()))
        n_wavelengths = len(first_spectra)

        # Create output array with shape (dim1, dim2, ..., n_wavelengths)
        cube_shape = list(self.grid_shape) + [n_wavelengths]
        spectra_cube = np.zeros(cube_shape)

        # Populate the cube
        for params, spectra in self.points.items():
            # Convert params to indices
            indices = []
            for i, value in enumerate(params):
                # Find index of this value in param_values[i]
                idx = np.where(np.isclose(self.param_values[i], value))[0][0]
                indices.append(idx)

            # Assign spectra to the correct position in the cube
            spectra_cube[tuple(indices)] = spectra

        return spectra_cube, self.param_values