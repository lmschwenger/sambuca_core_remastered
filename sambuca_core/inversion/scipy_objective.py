import numpy as np

from sambuca_core import forward_model
from sambuca_core.inversion.objective_functions import distance_f


class SciPyObjective:
    """An objective function for use with scipy.optimize.minimize."""

    def __init__(self,
                 sensor_filter,
                 fixed_parameters,
                 error_function=distance_f,
                 nedr=None):
        """Initialize the objective function.

        Args:
            sensor_filter: The sensor spectral filter.
            fixed_parameters: Fixed parameters for the forward model.
            error_function: The function to calculate error between observed and modeled spectra.
            nedr: Noise equivalent delta reflectance values for each band.
        """
        self.sensor_filter = sensor_filter
        self.fixed_parameters = fixed_parameters
        self.error_function = error_function
        self.nedr = nedr
        self._observed_rrs = None

    def __call__(self, params):
        """Calculate the error between observed and modeled spectra."""
        if self._observed_rrs is None:
            raise ValueError("Observed reflectance data not set")

        # Convert params to forward model inputs
        forward_model_params = self.fixed_parameters.get_forward_model_params(params)

        # Run forward model
        results = forward_model(**forward_model_params)

        # Calculate error with optional NEDR weighting
        if self.nedr is not None:
            # Apply NEDR weighting
            weights = 1.0 / (self.nedr ** 2)
            squared_diff = (results.rrs - self._observed_rrs) ** 2
            weighted_squared_diff = weights * squared_diff
            error = np.sqrt(np.sum(weighted_squared_diff) / np.sum(weights))
        else:
            # Standard RMSE if no NEDR provided
            error = np.sqrt(np.mean((results.rrs - self._observed_rrs) ** 2))

        return error