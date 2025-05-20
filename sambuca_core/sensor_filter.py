"""Functions for working with Sensor Filters."""

import os
from typing import Dict, List, Optional, Tuple, Union, Callable

import numpy as np
import pandas as pd
from numpy.typing import NDArray
import spectral.io.envi as envi
import spectral.io.spyfile as spyfile

from .exceptions import UnsupportedDataFormatError, DataValidationError
from .utility import list_files, strictly_increasing, merge_dictionary


def apply_sensor_filter(
    spectra: Union[List[float], NDArray[np.float64]],
    normalised_response_function: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Applies a sensor filter to a spectra using the given spectral response function.

    Args:
        spectra: The input spectra.
        normalised_response_function: The spectral sensitivity matrix.
            The first dimension determines the number of output bands.
            The second dimension represents the proportional contribution of
            each of the input bands to an output band. The size must match the
            number of bands in the input spectra.

    Returns:
        The filtered spectra as a 1D array if input was 1D, or a 2D array if input was 2D.
    """
    # Convert to numpy array if needed
    spectra_arr = np.asarray(spectra)

    # Check if input is 2D (multiple spectra)
    if spectra_arr.ndim > 1:
        # For 2D input, each column is a separate spectrum
        # Output will be a 2D array with shape (n_output_bands, n_spectra)
        return np.dot(
            normalised_response_function, spectra_arr
        ) / normalised_response_function.sum(axis=1, keepdims=True)
    else:
        # For 1D input (single spectrum), output will be a 1D array
        result = np.dot(
            normalised_response_function, spectra_arr
        ) / normalised_response_function.sum(axis=1)
        return result.flatten()  # Ensure output is 1D


def _validate_filter_dataframe(filter_dataframe: pd.DataFrame) -> bool:
    """Validate a sensor filter data frame.

    Args:
        filter_dataframe: The sensor filter dataframe.

    Returns:
        True if the filter is valid; otherwise False.
    """
    wavelengths = filter_dataframe.index

    if not wavelengths.is_monotonic_increasing:
        return False

    # Are the wavelength spacings acceptable?
    # For now, only sensor filters that are specified with exact
    # 1nm bands are supported.
    band_diffs = np.ediff1d(wavelengths)
    if band_diffs.min() < 1.0 or band_diffs.max() > 1.0:
        # TODO: log warning about interpolation/averaging not being supported
        return False

    # The dtype of every column needs to be a numpy-compatible number
    if len(filter_dataframe.select_dtypes(include=[np.number]).columns) != len(
        filter_dataframe.columns
    ):
        return False

    return True


def _normalise_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Normalises the spectral bands in a dataframe.

    Args:
        dataframe: The spectral data.

    Returns:
        The normalised spectral data.
    """
    # Per-band normalisation
    return dataframe / dataframe.max()


def load_sensor_filter_spectral_library(
    directory: str, base_filename: str, normalise: bool = False
) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Loads a single sensor filter from an ENVI spectral library.

    Args:
        directory: Directory containing the sensor filter file.
        base_filename: The filename without the extension or '.'
            preceding the extension.
        normalise: If true, the filter will be normalised.

    Returns:
        A tuple containing:
            - The band-centre wavelengths.
            - The sensor filter.

    Raises:
        IOError: If the file cannot be found or read.
        DataValidationError: If the spectral library fails validation.
    """
    base_filename = os.path.join(directory, base_filename)
    file_pattern = "{0}.{1}"

    # Load the spectral library
    try:
        spectral_library = envi.open(
            file_pattern.format(base_filename, "hdr"),
            file_pattern.format(base_filename, "lib"),
        )
    except spyfile.FileNotFoundError as exception:
        raise IOError(f"File not found: {base_filename}") from exception

    # Convert to a DataFrame
    dataframe = pd.DataFrame(
        spectral_library.spectra.transpose(), index=spectral_library.bands.centers
    )
    dataframe.columns = [
        f"Band {x + 1}" for x in range(len(dataframe.columns))
    ]

    if not _validate_filter_dataframe(dataframe):
        raise DataValidationError(
            f"Spectral library {base_filename} failed validation"
        )

    if normalise:
        dataframe = _normalise_dataframe(dataframe)

    return np.array(dataframe.index), dataframe.values.transpose()


def load_sensor_filters_excel(
    filename: str, normalise: bool = False, sheet_names: Optional[List[str]] = None
) -> Dict[str, Tuple[NDArray[np.float64], NDArray[np.float64]]]:
    """Loads sensor filters from an Excel file.

    Both new style XLSX and old-style XLS formats are supported.

    Args:
        filename: Full path to the Excel file.
        normalise: Determines whether the filter bands will be
            normalised after loading.
        sheet_names: Optional list of worksheet names to load.
            The default is to attempt to load all worksheets.

    Returns:
        A dictionary of 2-tuples of numpy arrays.
        The first element contains the band centre wavelengths of the input
        bands, while the second element contains the filter.
        Dictionary is keyed by filter name inferred from the sheet name.
    """
    sensor_filters = {}
    with pd.ExcelFile(filename) as excel_file:
        # Default is all sheets
        if not sheet_names:
            sheet_names = excel_file.sheet_names

        for sheet in sheet_names:
            try:
                dataframe = excel_file.parse(
                    sheet, index_col=0
                )
                # Validate the dataframe
                if not _validate_filter_dataframe(dataframe):
                    continue

                if normalise:
                    dataframe = _normalise_dataframe(dataframe)

                sensor_filters[sheet] = (
                    np.array(dataframe.index),
                    dataframe.values.transpose(),
                )

            except Exception:
                # Skip any sheets that can't be read properly
                continue

    return sensor_filters


def load_sensor_filters(
    path: str,
    normalise: bool = False,
    spectral_library_name_parser: Optional[Callable[[str], str]] = None
) -> Dict[str, Tuple[NDArray[np.float64], NDArray[np.float64]]]:
    """Loads all valid sensor filters from the given location.

    Args:
        path: The directory path to scan for sensor filters.
        normalise: Determines whether the filter bands will be
            normalised after loading.
        spectral_library_name_parser: If supplied, this function
            accepts a single string argument (the full path to a spectral
            library file) and returns the sensor filter name that will be used
            in the dictionary of results.

    Returns:
        A dictionary of 2-tuples of numpy arrays.
        The first element contains the band centre wavelengths of the input
        bands, while the second element contains the filter.
        Dictionary is keyed by filter name inferred from the sheet name.

    Raises:
        OSError: If the directory does not exist.
    """
    sensor_filters = {}
    new_filters = {}

    try:
        # Excel files
        for file in list_files(path, ["xls", "xlsx"]):
            new_filters = load_sensor_filters_excel(file, normalise=normalise)
            merge_dictionary(sensor_filters, new_filters)

        # Spectral Libraries
        for file in list_files(path, ["lib"]):
            base_name, _ = os.path.splitext(os.path.basename(file))

            if spectral_library_name_parser:
                name = spectral_library_name_parser(file)
            else:
                name = base_name

            loaded_filter = load_sensor_filter_spectral_library(
                path, base_name, normalise=normalise
            )

            if name not in sensor_filters:
                sensor_filters[name] = loaded_filter
    except UnsupportedDataFormatError:
        raise UnsupportedDataFormatError("Unsupported sensor filter format")

    return sensor_filters


def load_sensor_filter_from_csv(filename):
    """Load a sensor filter from a CSV file.

    Args:
        filename: Path to the CSV file containing the sensor filter.

    Returns:
        Tuple containing (wavelengths, filter_responses)
    """
    # Load the CSV file
    filter_df = pd.read_csv(filename, index_col=0)

    # Extract wavelengths and filter responses
    wavelengths = np.array(filter_df.index, dtype=float)
    filter_responses = np.array(filter_df.values, dtype=float).T  # Transpose to get bands as rows

    # Check validity (optional)
    if np.all(filter_responses == 0):
        raise ValueError("Filter responses are all zero. Check your CSV file.")

    return wavelengths, filter_responses