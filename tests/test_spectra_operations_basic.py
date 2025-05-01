"""Basic tests for the spectra operations functionality."""

import numpy as np
import pytest

import sambuca_core as sbc


def test_spectra_find_common_wavelengths():
    """Test finding common wavelengths between spectra."""
    # Create test spectra
    spectra1 = (np.array([400, 450, 500, 550, 600]), np.array([0.1, 0.2, 0.3, 0.4, 0.5]))
    spectra2 = (np.array([450, 500, 550, 600, 650]), np.array([0.2, 0.3, 0.4, 0.5, 0.6]))
    spectra3 = (np.array([500, 550, 600, 650, 700]), np.array([0.3, 0.4, 0.5, 0.6, 0.7]))

    # Find common wavelengths
    common = sbc.spectra_find_common_wavelengths(spectra1, spectra2, spectra3)

    # Expected common wavelengths: 500, 550, 600
    expected = np.array([500, 550, 600])

    # Check results
    assert len(common) == len(expected)
    assert np.all(common == expected)


def test_spectra_find_common_wavelengths_with_arrays():
    """Test finding common wavelengths when passing arrays directly."""
    # Create test wavelength arrays
    wavelengths1 = np.array([400, 450, 500, 550, 600])
    wavelengths2 = np.array([450, 500, 550, 600, 650])
    wavelengths3 = np.array([500, 550, 600, 650, 700])

    # Find common wavelengths
    common = sbc.spectra_find_common_wavelengths(wavelengths1, wavelengths2, wavelengths3)

    # Expected common wavelengths: 500, 550, 600
    expected = np.array([500, 550, 600])

    # Check results
    assert len(common) == len(expected)
    assert np.all(common == expected)


def test_spectra_find_common_wavelengths_no_common():
    """Test finding common wavelengths when there are none."""
    # Create test spectra with no overlap
    spectra1 = (np.array([400, 410, 420]), np.array([0.1, 0.2, 0.3]))
    spectra2 = (np.array([500, 510, 520]), np.array([0.4, 0.5, 0.6]))

    # Find common wavelengths
    common = sbc.spectra_find_common_wavelengths(spectra1, spectra2)

    # Expected: empty array
    assert len(common) == 0


def test_spectra_apply_wavelength_mask():
    """Test applying a wavelength mask to a spectra."""
    # Create test spectra
    wavelengths = np.array([400, 450, 500, 550, 600, 650, 700])
    values = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
    spectra = (wavelengths, values)

    # Create mask: only keep 500, 550, 600
    mask = np.array([500, 550, 600])

    # Apply mask
    masked_wavelengths, masked_values = sbc.spectra_apply_wavelength_mask(spectra, mask)

    # Expected results
    expected_wavelengths = np.array([500, 550, 600])
    expected_values = np.array([0.3, 0.4, 0.5])

    # Check results
    assert len(masked_wavelengths) == len(expected_wavelengths)
    assert len(masked_values) == len(expected_values)
    assert np.all(masked_wavelengths == expected_wavelengths)
    assert np.all(masked_values == expected_values)


def test_spectra_operations_combined():
    """Test the combined workflow of finding common wavelengths and applying a mask."""
    # Create test spectra with different wavelength ranges
    spectra1 = (np.array([400, 450, 500, 550, 600]), np.array([0.1, 0.2, 0.3, 0.4, 0.5]))
    spectra2 = (np.array([450, 500, 550, 600, 650]), np.array([0.2, 0.3, 0.4, 0.5, 0.6]))

    # Find common wavelengths
    common = sbc.spectra_find_common_wavelengths(spectra1, spectra2)

    # Expected common wavelengths: 450, 500, 550, 600
    expected_common = np.array([450, 500, 550, 600])
    assert np.all(common == expected_common)

    # Apply mask to both spectra
    masked_wavelengths1, masked_values1 = sbc.spectra_apply_wavelength_mask(spectra1, common)
    masked_wavelengths2, masked_values2 = sbc.spectra_apply_wavelength_mask(spectra2, common)

    # Check the masked spectra have the same wavelengths
    assert np.all(masked_wavelengths1 == masked_wavelengths2)

    # Check the values are correct
    assert np.all(masked_values1 == np.array([0.2, 0.3, 0.4, 0.5]))
    assert np.all(masked_values2 == np.array([0.2, 0.3, 0.4, 0.5]))