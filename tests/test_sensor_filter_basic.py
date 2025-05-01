"""Basic tests for the sensor filter functionality."""

import numpy as np
import pytest

import sambuca_core as sbc


def test_apply_sensor_filter():
    """Test the basic sensor filter application functionality."""
    # Create synthetic input spectra (551 bands as in the original tests)
    num_bands = 551
    input_spectra = np.linspace(0.01, 0.1, num_bands)

    # Create a simple 3-band filter that takes averages of specific ranges
    filter_matrix = np.zeros((3, num_bands))

    # Filter 1: average of first third
    filter_matrix[0, 0:num_bands//3] = 1.0

    # Filter 2: average of middle third
    filter_matrix[1, num_bands//3:2*num_bands//3] = 1.0

    # Filter 3: average of last third
    filter_matrix[2, 2*num_bands//3:] = 1.0

    # Apply the filter
    filtered_spectra = sbc.apply_sensor_filter(input_spectra, filter_matrix)

    # Check dimensions - should be 1D when input is 1D
    assert filtered_spectra.shape == (3,)

    # Manually calculate expected results
    expected_1 = np.mean(input_spectra[0:num_bands//3])
    expected_2 = np.mean(input_spectra[num_bands//3:2*num_bands//3])
    expected_3 = np.mean(input_spectra[2*num_bands//3:])

    # Check results
    assert np.isclose(filtered_spectra[0], expected_1)
    assert np.isclose(filtered_spectra[1], expected_2)
    assert np.isclose(filtered_spectra[2], expected_3)

    # Test with 2D input spectra to ensure that works too
    input_spectra_2d = np.column_stack([input_spectra, input_spectra * 2])
    filtered_spectra_2d = sbc.apply_sensor_filter(input_spectra_2d, filter_matrix)

    # Should return 2D result for 2D input
    assert filtered_spectra_2d.shape == (3, 2)

    # First column should match our previous result
    assert np.allclose(filtered_spectra_2d[:, 0], filtered_spectra)
    # Second column should be double the first
    assert np.allclose(filtered_spectra_2d[:, 1], filtered_spectra * 2)


def test_apply_sensor_filter_nonuniform_weights():
    """Test sensor filter with non-uniform weights."""
    # Create synthetic input spectra
    num_bands = 10
    input_spectra = np.linspace(0.01, 0.1, num_bands)

    # Create a simple 2-band filter with non-uniform weights
    filter_matrix = np.zeros((2, num_bands))

    # Filter 1: weighted average of first half (triangular weights)
    weights1 = np.linspace(0.1, 1.0, num_bands//2)
    filter_matrix[0, 0:num_bands//2] = weights1

    # Filter 2: weighted average of second half (gaussian-like weights)
    center = 7
    sigma = 1.0
    x = np.arange(num_bands//2, num_bands)
    weights2 = np.exp(-0.5 * ((x - center) / sigma) ** 2)
    filter_matrix[1, num_bands//2:] = weights2

    # Apply the filter
    filtered_spectra = sbc.apply_sensor_filter(input_spectra, filter_matrix)

    # Check dimensions - should be 1D for 1D input
    assert filtered_spectra.shape == (2,)

    # Manually calculate expected results
    expected_1 = np.sum(input_spectra[0:num_bands//2] * weights1) / np.sum(weights1)
    expected_2 = np.sum(input_spectra[num_bands//2:] * weights2) / np.sum(weights2)

    # Check results
    assert np.isclose(filtered_spectra[0], expected_1)
    assert np.isclose(filtered_spectra[1], expected_2)