"""Look-up table based inversion for Sambuca with optimized performance.

This module provides a LUT-based approach for fast inversion of the Sambuca
forward model with optimizations for performance, especially memory usage
and lookup speed.
"""

import os
import pickle
import itertools
import numpy as np
from numpy.typing import NDArray
from tqdm import tqdm
from typing import Dict, List, Tuple, Union, Optional, Any
import time
from scipy.spatial import cKDTree

from ..forward_model import forward_model
from .parameters import InversionParameters
from .optimization import invert_spectrum, multi_start_inversion


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
        self.param_array = None  # Array form of parameters for KD-tree
        self.spectra_array = None  # Array form of spectra for faster lookup
        self.kdtree = None  # KD-tree for fast nearest neighbor lookups
        self.table_built = False
        self.grid_shape = None  # Shape of the parameter grid
        self.param_values = []  # List of parameter values for each dimension
        self.in_memory = True  # Whether the full LUT is kept in memory
        self.lut_file = None  # Path to LUT file if using disk-based mode

    def build_table(
            self,
            grid_size: Union[int, List[int]] = 10,
            progress_bar: bool = True,
            memory_optimized: bool = False,
            use_kdtree: bool = True,
            batch_size: int = 1000,
    ) -> None:
        """Build the look-up table by running the forward model for parameter combinations.

        Args:
            grid_size: Number of points along each parameter dimension (can be int or list).
            progress_bar: Whether to show a progress bar.
            memory_optimized: If True, reduce memory usage by not keeping all spectra in a dict.
            use_kdtree: Whether to build a KD-tree for faster lookups.
            batch_size: Number of parameter combinations to process in each batch.

        Raises:
            ValueError: If no parameters are specified for inversion.
        """
        start_time = time.time()

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

        # Convert to arrays for faster operations
        self.param_array = np.array(param_combinations)
        first_spectral_length = len(self.inversion_parameters.wavelengths)
        self.spectra_array = np.zeros((total_combinations, first_spectral_length))

        # Process in batches to avoid memory issues
        n_batches = (total_combinations + batch_size - 1) // batch_size

        if progress_bar:
            batch_iterator = tqdm(range(n_batches), desc="Building LUT")
        else:
            batch_iterator = range(n_batches)

        # Process each batch
        for batch_idx in batch_iterator:
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, total_combinations)

            for i in range(start_idx, end_idx):
                params = tuple(self.param_array[i])

                # Run forward model
                fwd_params = self.inversion_parameters.get_forward_model_params(list(params))
                results = forward_model(**fwd_params)

                # Store results
                if not memory_optimized:
                    self.points[params] = results.rrs

                self.spectra_array[i] = results.rrs

        # Keep memory optimization setting
        self.in_memory = not memory_optimized

        # Build KD-tree for faster lookups if requested
        if use_kdtree:
            if progress_bar:
                print("Building KD-tree for fast lookups...")

            self.kdtree = cKDTree(self.spectra_array)

        self.table_built = True
        elapsed_time = time.time() - start_time
        print(f"Look-up table built with {total_combinations} parameter combinations in {elapsed_time:.2f} seconds")

        # Print memory usage estimate
        param_mem = self.param_array.nbytes / (1024 * 1024)
        spectra_mem = self.spectra_array.nbytes / (1024 * 1024)
        total_mem = param_mem + spectra_mem

        if not memory_optimized:
            dict_mem = total_combinations * (first_spectral_length * 8 + 64) / (1024 * 1024)  # Rough estimate
            total_mem += dict_mem

        print(f"Estimated memory usage: {total_mem:.2f} MB")

    def save(self, filename: str, compressed: bool = True) -> None:
        """Save the look-up table to a file.

        Args:
            filename: Path to save the LUT.
            compressed: Whether to use compressed format (slower but smaller file).
        """
        self.lut_file = filename

        if compressed:
            # Use numpy's compressed format for arrays
            np.savez_compressed(
                filename + "_arrays",
                param_array=self.param_array,
                spectra_array=self.spectra_array,
                grid_shape=np.array(self.grid_shape),
            )

            # Save parameter values separately
            param_values_dict = {f"param_values_{i}": values for i, values in enumerate(self.param_values)}
            np.savez_compressed(filename + "_param_values", **param_values_dict)

            # Save other attributes with pickle
            attrs_to_save = {
                'inversion_parameters': self.inversion_parameters,
                'param_names': self.param_names,
                'bounds': self.bounds,
                'table_built': self.table_built,
                'in_memory': self.in_memory,
            }

            with open(filename + "_attrs", 'wb') as f:
                pickle.dump(attrs_to_save, f)

            print(f"Look-up table saved to {filename} (split into multiple files)")

        else:
            # Standard pickle approach (all in one file)
            data_to_save = {
                'inversion_parameters': self.inversion_parameters,
                'param_names': self.param_names,
                'bounds': self.bounds,
                'param_array': self.param_array,
                'spectra_array': self.spectra_array,
                'points': self.points if self.in_memory else None,
                'table_built': self.table_built,
                'grid_shape': self.grid_shape,
                'param_values': self.param_values,
                'in_memory': self.in_memory,
            }

            with open(filename, 'wb') as f:
                pickle.dump(data_to_save, f)

            print(f"Look-up table saved to {filename}")

    @classmethod
    def load(cls, filename: str, build_kdtree: bool = True, in_memory: bool = None) -> 'LookUpTable':
        """Load a look-up table from a file.

        Args:
            filename: Path to the saved LUT file.
            build_kdtree: Whether to build a KD-tree after loading for faster lookups.
            in_memory: Override the saved setting for keeping points dictionary in memory.

        Returns:
            Loaded LookUpTable object.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        load_start = time.time()

        # Check if this is a split compressed format
        is_compressed = os.path.exists(filename + "_arrays.npz")

        if is_compressed:
            # Load arrays
            arrays_data = np.load(filename + "_arrays.npz")
            param_array = arrays_data['param_array']
            spectra_array = arrays_data['spectra_array']
            grid_shape = tuple(arrays_data['grid_shape'])

            # Load parameter values
            param_values_data = np.load(filename + "_param_values.npz")
            param_values = []
            i = 0
            while f"param_values_{i}" in param_values_data:
                param_values.append(param_values_data[f"param_values_{i}"])
                i += 1

            # Load other attributes
            with open(filename + "_attrs", 'rb') as f:
                attrs_data = pickle.load(f)

            # Create instance
            lut = cls(attrs_data['inversion_parameters'])
            lut.param_names = attrs_data['param_names']
            lut.bounds = attrs_data['bounds']
            lut.table_built = attrs_data['table_built']
            lut.in_memory = in_memory if in_memory is not None else attrs_data['in_memory']
            lut.param_array = param_array
            lut.spectra_array = spectra_array
            lut.grid_shape = grid_shape
            lut.param_values = param_values
            lut.lut_file = filename

            # Reconstruct points dictionary if needed
            if lut.in_memory:
                lut.points = {}
                for i, params in enumerate(param_array):
                    lut.points[tuple(params)] = spectra_array[i]
        else:
            # Standard pickle format
            if not os.path.exists(filename):
                raise FileNotFoundError(f"Look-up table file {filename} not found")

            with open(filename, 'rb') as f:
                data = pickle.load(f)

            lut = cls(data['inversion_parameters'])
            lut.param_names = data['param_names']
            lut.bounds = data['bounds']
            lut.param_array = data['param_array']
            lut.spectra_array = data['spectra_array']
            lut.table_built = data['table_built']
            lut.grid_shape = data['grid_shape']
            lut.param_values = data['param_values']
            lut.in_memory = in_memory if in_memory is not None else data['in_memory']
            lut.lut_file = filename

            # Load points if available and needed
            if lut.in_memory:
                if data['points'] is not None:
                    lut.points = data['points']
                else:
                    # Reconstruct from arrays
                    lut.points = {}
                    for i, params in enumerate(lut.param_array):
                        lut.points[tuple(params)] = lut.spectra_array[i]

        # Build KD-tree if requested
        if build_kdtree:
            print("Building KD-tree for fast lookups...")
            lut.kdtree = cKDTree(lut.spectra_array)

        load_time = time.time() - load_start
        print(f"Look-up table loaded in {load_time:.2f} seconds")
        print(f"LUT contains {len(lut.param_array)} parameter combinations")

        return lut

    # Replace the entire invert method in sambuca_core/inversion/lut.py

    def invert(
            self,
            observed_rrs: NDArray[np.float64],
            metric: str = 'rmse',
            refine: bool = True,
            n_best: int = 1,
            use_kdtree: bool = True,
            use_multi_start: bool = False,
            n_starts: int = 5,
            nedr: Optional[NDArray[np.float64]] = None
    ) -> Dict[str, Any]:
        """Invert observed reflectance using the look-up table with optimized performance.

        Args:
            observed_rrs: Observed remote sensing reflectance.
            metric: Error metric ('rmse', 'sam' [Spectral Angle Mapper], or 'Euclidean').
            refine: Whether to refine the result with local optimization.
            n_best: Number of best matches to consider for refinement.
            use_kdtree: Whether to use KD-tree for fast lookups (if available).
            nedr: Noise equivalent delta reflectance for weighting.

        Returns:
            Dictionary with inverted parameters and metadata.

        Raises:
            ValueError: If the look-up table has not been built yet or if
                an unknown metric is specified.
                :param nedr:
                :param observed_rrs:
                :param n_best:
                :param use_kdtree:
                :param metric:
                :param refine:
                :param n_starts:
                :param use_multi_start:
        """
        if not self.table_built:
            raise ValueError("Look-up table not built yet, call build_table() first")

        start_time = time.time()

        # Use KD-tree for fast lookups if available and requested
        if use_kdtree and self.kdtree is not None and metric in ['rmse', 'euclidean']:
            # For RMSE and euclidean, we can use KD-tree directly
            distances, indices = self.kdtree.query(observed_rrs, k=n_best)

            # Handle the case where k=1 returns scalars instead of arrays
            if n_best == 1:
                distances = [distances]
                indices = [indices]
            else:
                # Ensure we have lists for consistency
                distances = list(distances)
                indices = list(indices)

            # Get parameters and spectra for best matches
            best_params = [tuple(self.param_array[i]) for i in indices]
            best_spectra = [self.spectra_array[i] for i in indices]
            best_errors = distances

        else:
            # Traditional approach - calculate all errors
            if self.in_memory and self.points:
                # Use dictionary approach
                errors = []
                params_list = []
                spectra_list = []

                for params, spectra in self.points.items():
                    if metric == 'rmse':
                        if nedr is not None:
                            # NEDR-weighted RMSE
                            weights = 1.0 / (nedr ** 2)
                            weighted_squared_diff = weights * ((spectra - observed_rrs) ** 2)
                            error = np.sqrt(np.sum(weighted_squared_diff) / np.sum(weights))
                        else:
                            # Standard RMSE
                            error = np.sqrt(np.mean((spectra - observed_rrs) ** 2))
                    elif metric == 'euclidean':
                        error = np.sqrt(np.sum((spectra - observed_rrs) ** 2))
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

            else:
                # Use array approach for memory efficiency
                errors = np.zeros(len(self.param_array))

                for i, spectra in enumerate(self.spectra_array):
                    if metric == 'rmse':
                        errors[i] = np.sqrt(np.mean((spectra - observed_rrs) ** 2))
                    elif metric == 'euclidean':
                        errors[i] = np.sqrt(np.sum((spectra - observed_rrs) ** 2))
                    elif metric == 'sam':
                        dot_product = np.sum(spectra * observed_rrs)
                        norm_product = np.sqrt(np.sum(spectra ** 2) * np.sum(observed_rrs ** 2))
                        if norm_product < 1e-10:
                            errors[i] = np.pi / 2
                        else:
                            errors[i] = np.arccos(np.clip(dot_product / norm_product, -1.0, 1.0))

                # Sort by error
                best_indices = np.argsort(errors)[:n_best]
                best_errors = [errors[i] for i in best_indices]
                best_params = [tuple(self.param_array[i]) for i in best_indices]
                best_spectra = [self.spectra_array[i] for i in best_indices]

        lookup_time = time.time() - start_time

        # Optional refinement using optimization
        if refine:
            refine_start = time.time()

            # Use the best LUT match as initial values
            initial_values = list(best_params[0])

            # Run optimization (either single or multi-start)
            if use_multi_start:
                result = multi_start_inversion(
                    observed_rrs,
                    self.inversion_parameters,
                    n_starts=n_starts,
                    method='L-BFGS-B',
                    options={'maxiter': 50}
                )
            else:
                result = invert_spectrum(
                    observed_rrs,
                    self.inversion_parameters,
                    initial_values=initial_values,
                    method='L-BFGS-B',
                    options={'maxiter': 50}
                )

            refine_time = time.time() - refine_start

            # Convert best LUT parameters to dictionary
            lut_params_dict = {}
            for i, param_name in enumerate(self.param_names):
                lut_params_dict[param_name] = best_params[0][i]

            # Return optimization results with timing info
            return {
                'parameters': result.parameters,
                'error': result.objective_value,
                'modeled_spectra': result.modeled_spectra,
                'lut_parameters': lut_params_dict,
                'lut_error': best_errors[0],
                'lut_spectra': best_spectra[0],
                'forward_model_results': result.forward_model_results,
                'timing': {
                    'lookup': lookup_time,
                    'refinement': refine_time,
                    'total': lookup_time + refine_time
                }
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
            'timing': {
                'lookup': lookup_time,
                'total': lookup_time
            }
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
        n_wavelengths = self.spectra_array.shape[1]

        # Create output array with shape (dim1, dim2, ..., n_wavelengths)
        cube_shape = list(self.grid_shape) + [n_wavelengths]
        spectra_cube = np.zeros(cube_shape)

        # Populate the cube
        for i, params in enumerate(self.param_array):
            # Convert params to indices
            indices = []
            for j, value in enumerate(params):
                # Find index of this value in param_values[j]
                idx = np.where(np.isclose(self.param_values[j], value))[0][0]
                indices.append(idx)

            # Assign spectra to the correct position in the cube
            spectra_cube[tuple(indices)] = self.spectra_array[i]

        return spectra_cube, self.param_values
