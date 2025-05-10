"""Core components of the Sambuca modeling system.

Sambuca is a Semi-Analytical Model for Bathymetry, Un-mixing, and Concentration Assessment
(SAMBUCA) developed by CSIRO for remote sensing applications.
"""

from typing import Tuple, Dict, List

# Import public functionality
from .exceptions import (
    SambucaException,
    UnsupportedDataFormatError,
    DataValidationError,
)
from .forward_model import forward_model, ForwardModelResults
from .sensor_filter import (
    truncate_filter_to_wavelengths,
    interpolate_filter_to_wavelengths,
    normalize_filter_response,
    validate_sensor_filter,
    apply_sensor_filter_with_validation,
)
from .siop_manager import SIOPManager
from .spectra_operations import (
    spectra_find_common_wavelengths,
    spectra_apply_wavelength_mask,
)
from .spectra_readers import (
    load_spectral_library,
    load_all_spectral_libraries,
    load_csv_spectral_library,
    load_envi_spectral_library,
    load_excel_spectral_library,
)
from .utility import (
    strictly_decreasing,
    strictly_increasing,
)

from .preparation import prepare_spectral_inputs

__author__ = "Lasse M. Schwenger"
__email__ = "lasse.m.schwenger@gmail.com"
__version__ = "0.1.0"

# Type definitions for documentation
Spectra = Tuple[List[float], List[float]]
SpectraDict = Dict[str, Spectra]