"""Functions for loading collections of spectra from files.

This module contains functions for loading spectra from various file formats
including ENVI spectral libraries, CSV files, and Excel files.
"""

import os
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from numpy.typing import NDArray
import spectral.io.envi as envi
import spectral.io.spyfile as spyfile

from .exceptions import UnsupportedDataFormatError, DataValidationError
from .utility import list_files, strictly_increasing, merge_dictionary


def _validate_spectra_dataframe(spectra_dataframe: pd.DataFrame) -> bool:
    """Validate a spectra data frame.

    Args:
        spectra_dataframe: The spectra data frame to validate.

    Returns:
        True if the spectra is valid; otherwise False.
    """
    wavelengths = spectra_dataframe.index

    # Are the band-centre wavelengths strictly increasing?
    if not strictly_increasing(wavelengths):
        return False

    # Are the wavelength spacings acceptable?
    # For now, only spectra that are specified with exact
    # 1nm bands are supported.
    band_diffs = np.ediff1d(wavelengths)
    if band_diffs.min() < 1.0 or band_diffs.max() > 1.0:
        # TODO: log warning about interpolation/averaging not being supported
        return False

    # The dtype of every column needs to be a numpy-compatible number
    if len(spectra_dataframe.select_dtypes(include=[np.number]).columns) != len(
        spectra_dataframe.columns
    ):
        return False

    return True


def _add_dataframe_spectra_to_dictionary(
    dataframe: pd.DataFrame,
    base_name: str,
    dictionary: Optional[Dict[str, Tuple[NDArray[np.float64], NDArray[np.float64]]]] = None
) -> Dict[str, Tuple[NDArray[np.float64], NDArray[np.float64]]]:
    """Adds all spectra from a dataframe to a dictionary.

    The spectra name is built as 'base_name:column_name'.

    Args:
        dataframe: The dataframe containing spectra data.
        base_name: The base name for the spectra.
        dictionary: Optional existing dictionary to add to.

    Returns:
        A dictionary with the spectra added.
    """
    dictionary = {} if dictionary is None else dictionary
    for column in dataframe:
        dictionary[f"{base_name.lower()}:{column}"] = (
            np.array(dataframe.index),
            dataframe[column].values,
        )
    return dictionary


def load_csv_spectral_library(
    filename: str, validate: bool = True
) -> Dict[str, Tuple[NDArray[np.float64], NDArray[np.float64]]]:
    """Loads a spectral library from a CSV file.

    The CSV file must have a header row, and the wavelengths must be the first
    column.

    Args:
        filename: Full path to the CSV file.
        validate: If true, data validation will be performed.

    Returns:
        A dictionary of 2-tuples of numpy arrays.
        The first element contains the band centre wavelengths,
        while the second element contains the spectra.
        The dictionary is keyed by spectra name, formed by concatenation
        of the file and band names. This allows multiple spectra from
        multiple files to be unambiguously collected into a dictionary.
        Note that the filename component is always converted to lower case.

    Raises:
        DataValidationError: If the file fails validation.
    """
    dataframe = pd.read_csv(filename, index_col=0)
    if validate and not _validate_spectra_dataframe(dataframe):
        raise DataValidationError(f"{filename} failed validation")

    base_name, _ = os.path.splitext(os.path.basename(filename))
    return _add_dataframe_spectra_to_dictionary(dataframe, base_name)


def load_excel_spectral_library(
    filename: str,
    sheet_names: Optional[List[str]] = None,
    validate: bool = True
) -> Dict[str, Tuple[NDArray[np.float64], NDArray[np.float64]]]:
    """Loads a spectral library from an Excel file.

    Both new style XLSX and old-style XLS formats are supported.

    Args:
        filename: Full path to the Excel file.
        sheet_names: Optional list of worksheet names to load.
            The default is to attempt to load all worksheets.
        validate: If true, data validation will be performed.

    Returns:
        A dictionary of 2-tuples of numpy arrays.
        The first element contains the band centre wavelengths,
        while the second element contains the spectra.
        The dictionary is keyed by spectra name, formed by concatenation
        of the file and band names. This allows multiple spectra from
        multiple files to be unambiguously collected into a dictionary.
        Note that the filename component is always converted to lower case.
    """
    all_spectra = {}
    with pd.ExcelFile(filename) as excel_file:
        base_name, _ = os.path.splitext(os.path.basename(filename))
        # Default is all sheets
        if not sheet_names:
            sheet_names = excel_file.sheet_names

        for sheet in sheet_names:
            try:
                dataframe = excel_file.parse(
                    sheet, index_col=0
                )
                # Validate the dataframe
                if validate and not _validate_spectra_dataframe(dataframe):
                    continue

                all_spectra = _add_dataframe_spectra_to_dictionary(
                    dataframe, base_name, all_spectra
                )
            except Exception:
                # Skip any sheets that can't be read properly
                continue

    return all_spectra


def load_envi_spectral_library(
    directory: str, base_filename: str, validate: bool = True
) -> Dict[str, Tuple[NDArray[np.float64], NDArray[np.float64]]]:
    """Loads spectra from an ENVI spectral library.

    Args:
        directory: Directory containing the spectral library file.
        base_filename: The filename without the extension or '.'
            preceding the extension.
        validate: If true, data validation will be performed.

    Returns:
        A dictionary of 2-tuples of numpy arrays.
        The first element contains the band centre wavelengths,
        while the second element contains the spectra.
        The dictionary is keyed by spectra name, formed by concatenation
        of the file and band names. This allows multiple spectra from
        multiple files to be unambiguously collected into a dictionary.
        Note that the filename component is always converted to lower case.

    Raises:
        IOError: If the file cannot be found or read.
        DataValidationError: If the file fails validation.
    """
    full_filename = os.path.join(directory, base_filename)
    file_pattern = "{0}.{1}"

    # Load the spectral library
    try:
        spectral_library = envi.open(
            file_pattern.format(full_filename, "hdr"),
            file_pattern.format(full_filename, "lib"),
        )
    except spyfile.FileNotFoundError as exception:
        raise IOError(f"File not found: {full_filename}") from exception

    # Convert to a DataFrame for processing
    dataframe = pd.DataFrame(
        spectral_library.spectra.transpose(), index=spectral_library.bands.centers
    )
    dataframe.columns = spectral_library.names

    if validate and not _validate_spectra_dataframe(dataframe):
        raise DataValidationError(
            f"Spectral library {base_filename} failed validation"
        )

    # Merge the spectra into a dictionary
    return _add_dataframe_spectra_to_dictionary(dataframe, base_filename)


def load_all_spectral_libraries(
    path: str, validate: bool = True
) -> Dict[str, Tuple[NDArray[np.float64], NDArray[np.float64]]]:
    """Loads all valid spectra from the given location.

    Args:
        path: The directory path to scan for supported spectra files.
        validate: If true, data validation will be performed.

    Returns:
        A dictionary of 2-tuples of numpy arrays.
        The first element contains the band centre wavelengths of the input
        bands, while the second element contains the spectra values.
        Dictionary is keyed by spectra name built from the file and
        band/sheet names, separated by a colon.

        Note that names are not disambiguated, so that if more than one
        filter has the same name, only the first will be returned and no
        error will be raised.

        Note that the filename component is always converted to lower case.
        This is required for consistent results on different platforms.

    Raises:
        OSError: If the directory does not exist.
    """
    all_spectra = {}
    new_spectra = {}

    # Excel files
    for file in list_files(path, ["xls", "xlsx"]):
        try:
            new_spectra = load_excel_spectral_library(file, validate=validate)
        except UnsupportedDataFormatError:
            pass
        merge_dictionary(all_spectra, new_spectra)

    # CSV files
    for file in list_files(path, ["csv"]):
        try:
            new_spectra = load_csv_spectral_library(file, validate=validate)
        except UnsupportedDataFormatError:
            pass
        merge_dictionary(all_spectra, new_spectra)

    # Spectral Libraries
    for file in list_files(path, ["lib"]):
        try:
            base_name, _ = os.path.splitext(os.path.basename(file))
            new_spectra = load_envi_spectral_library(path, base_name, validate=validate)
        except UnsupportedDataFormatError:
            pass
        merge_dictionary(all_spectra, new_spectra)

    return all_spectra


def load_spectral_library(
    filename: str, validate: bool = True
) -> Dict[str, Tuple[NDArray[np.float64], NDArray[np.float64]]]:
    """Loads a single spectral library from the given file name from any
    supported format (selected by file extension).

    Args:
        filename: Full path to the file.
        validate: If true, data validation will be performed.

    Returns:
        A dictionary of 2-tuples of numpy arrays.
        The first element contains the band centre wavelengths of the input
        bands, while the second element contains the spectra values.
        Dictionary is keyed by spectra name built from the file and
        band/sheet names, separated by a colon.
        For example: ``Moreton_Bay_speclib:white_sand``

        Note that names are not disambiguated, so that if more than one
        filter has the same name, only the first will be returned and no
        error will be raised.

        Note that the filename component is always converted to lower case.
        This is required for consistent results on different platforms.

    Raises:
        IOError: If the file does not exist.
        UnsupportedDataFormatError: If the file format is not supported.
    """
    if not os.path.isfile(filename):
        raise IOError(f"File does not exist: {filename}")

    base_name, extension = os.path.splitext(os.path.basename(filename))
    extension = extension[1:].lower()

    # Excel
    if extension in ["xls", "xlsx"]:
        return load_excel_spectral_library(filename, validate=validate)
    # CSV
    elif extension in ["csv"]:
        return load_csv_spectral_library(filename, validate=validate)
    # ENVI Spectral Libraries
    elif extension in ["hdr", "lib"]:
        return load_envi_spectral_library(
            os.path.dirname(filename), base_name, validate=validate
        )
    else:
        raise UnsupportedDataFormatError(
            f"File format {extension} is not supported"
        )