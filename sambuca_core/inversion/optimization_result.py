from dataclasses import dataclass
from typing import Dict, Any

import numpy as np
from numpy.typing import NDArray

from sambuca_core import ForwardModelResults


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
