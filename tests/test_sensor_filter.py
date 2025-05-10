"""Unit tests for sensor filter handling functions."""

import unittest
import numpy as np
from numpy.testing import assert_array_almost_equal, assert_array_equal
import os
import sys

# Add path to sambuca_core if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sambuca_core as sbc
from sambuca_core.sensor_filter import (
    truncate_filter_to_wavelengths,
    interpolate_filter_to_wavelengths,
    normalize_filter_response,
    validate_sensor_filter,
    apply_sensor_filter_with_validation
)


class TestSensorFilter(unittest.TestCase):
    """Test case for sensor filter functions."""

    def setUp(self):
        """Set up test data."""
        # Create a simple 3-band sensor filter
        self.wavelengths = np.array([400, 410, 420, 430, 440, 450, 460, 470, 480, 490, 500])
        self.filter_response = np.zeros((3, len(self.wavelengths)))

        # Band 1: Blue (centered at 450)
        self.filter_response[0, :] = np.array([0.0, 0.0, 0.1, 0.3, 0.5, 1.0, 0.5, 0.3, 0.1, 0.0, 0.0])

        # Band 2: Green (centered at 470)
        self.filter_response[1, :] = np.array([0.0, 0.0, 0.0, 0.0, 0.1, 0.3, 0.7, 1.0, 0.7, 0.3, 0.1])

        # Band 3: Red (centered at 490)
        self.filter_response[2, :] = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.3, 0.7, 1.0, 0.7])

        self.sensor_filter = (self.wavelengths, self.filter_response)

        # Create some test spectra
        self.test_spectrum = np.array([0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11])
        self.test_spectrum_2d = np.column_stack([self.test_spectrum, self.test_spectrum * 2])

    def test_truncate_filter_to_wavelengths(self):
        """Test truncation of filter to specific wavelength range."""
        # Create target wavelength range (subset of full range)
        target_wavelengths = np.array([430, 440, 450, 460, 470, 480])

        # Truncate the filter
        truncated_wavelengths, truncated_response = truncate_filter_to_wavelengths(
            self.sensor_filter, target_wavelengths)

        # Check that the right wavelengths were kept
        expected_wavelengths = np.array([430, 440, 450, 460, 470, 480])
        assert_array_equal(truncated_wavelengths, expected_wavelengths)

        # Check that the response matrix was correctly truncated
        expected_response = self.filter_response[:, 3:9]
        assert_array_equal(truncated_response, expected_response)

    def test_interpolate_filter_to_wavelengths(self):
        """Test interpolation of filter to new wavelength points."""
        # Create target wavelength range with different sampling
        target_wavelengths = np.array([425, 435, 445, 455, 465, 475, 485, 495])

        # Interpolate the filter
        interpolated_wavelengths, interpolated_response = interpolate_filter_to_wavelengths(
            self.sensor_filter, target_wavelengths)

        # Check wavelengths
        assert_array_equal(interpolated_wavelengths, target_wavelengths)

        # We won't check exact values for interpolation, but some basic checks
        self.assertEqual(interpolated_response.shape, (3, len(target_wavelengths)))

        # Band peaks should still be near the expected wavelengths
        band1_peak = target_wavelengths[np.argmax(interpolated_response[0, :])]
        band2_peak = target_wavelengths[np.argmax(interpolated_response[1, :])]
        band3_peak = target_wavelengths[np.argmax(interpolated_response[2, :])]

        self.assertTrue(445 <= band1_peak <= 455)  # Peak near 450nm
        self.assertTrue(465 <= band2_peak <= 475)  # Peak near 470nm
        self.assertTrue(485 <= band3_peak <= 495)  # Peak near 490nm

    def test_normalize_filter_response(self):
        """Test normalization of filter response."""
        # Test max normalization
        _, normalized_max = normalize_filter_response(self.sensor_filter, method='max')

        # Each band should have a maximum value of 1.0
        for i in range(3):
            self.assertEqual(np.max(normalized_max[i, :]), 1.0)

        # Test sum normalization
        _, normalized_sum = normalize_filter_response(self.sensor_filter, method='sum')

        # Each band should sum to 1.0
        for i in range(3):
            self.assertAlmostEqual(np.sum(normalized_sum[i, :]), 1.0)

    def test_validate_sensor_filter(self):
        """Test sensor filter validation."""
        # Valid filter should pass
        self.assertTrue(validate_sensor_filter(self.sensor_filter))

        # Test invalid wavelengths (not 1D)
        invalid_wavelengths = np.column_stack([self.wavelengths, self.wavelengths])
        invalid_filter = (invalid_wavelengths, self.filter_response)
        self.assertFalse(validate_sensor_filter(invalid_filter))

        # Test invalid response (not 2D)
        invalid_response = self.filter_response[0, :]  # Just 1D
        invalid_filter = (self.wavelengths, invalid_response)
        self.assertFalse(validate_sensor_filter(invalid_filter))

        # Test mismatched dimensions
        invalid_filter = (self.wavelengths[:-1], self.filter_response)
        self.assertFalse(validate_sensor_filter(invalid_filter))

        # Test non-monotonic wavelengths
        non_monotonic = np.array([400, 410, 420, 410, 440, 450, 460, 470, 480, 490, 500])
        invalid_filter = (non_monotonic, self.filter_response)
        self.assertFalse(validate_sensor_filter(invalid_filter))

        # Test negative response values
        negative_response = self.filter_response.copy()
        negative_response[1, 5] = -0.1
        invalid_filter = (self.wavelengths, negative_response)
        self.assertFalse(validate_sensor_filter(invalid_filter))

    def test_apply_sensor_filter_with_validation(self):
        """Test application of sensor filter with validation."""
        # Apply filter to 1D spectrum
        filtered_1d = apply_sensor_filter_with_validation(
            self.test_spectrum, self.sensor_filter)

        # Check shape
        self.assertEqual(filtered_1d.shape, (3,))

        # Manual calculation for verification
        expected_1d = np.zeros(3)
        for i in range(3):
            expected_1d[i] = np.sum(self.filter_response[i, :] * self.test_spectrum) / np.sum(
                self.filter_response[i, :])

        assert_array_almost_equal(filtered_1d, expected_1d)

        # Apply filter to 2D spectra (multiple spectra)
        filtered_2d = apply_sensor_filter_with_validation(
            self.test_spectrum_2d, self.sensor_filter)

        # Check shape
        self.assertEqual(filtered_2d.shape, (3, 2))

        # Manual calculation for verification
        expected_2d = np.zeros((3, 2))
        for i in range(3):
            for j in range(2):
                expected_2d[i, j] = np.sum(self.filter_response[i, :] * self.test_spectrum_2d[:, j]) / np.sum(
                    self.filter_response[i, :])

        assert_array_almost_equal(filtered_2d, expected_2d)

        # Test validation failure
        invalid_filter = (self.wavelengths[:-1], self.filter_response)
        with self.assertRaises(ValueError):
            apply_sensor_filter_with_validation(
                self.test_spectrum, invalid_filter, validate=True)


class TestPrepareSpectralInputs(unittest.TestCase):
    """Test case for the prepare_spectral_inputs function."""

    def setUp(self):
        """Set up test data."""
        # Create wavelengths and spectral data
        self.wavelengths1 = np.arange(400, 501, 5)  # 400-500nm in 5nm steps
        self.wavelengths2 = np.arange(420, 601, 5)  # 420-600nm in 5nm steps
        self.wavelengths3 = np.arange(380, 531, 5)  # 380-530nm in 5nm steps

        # Create values for these wavelengths
        self.values1 = np.sin(np.pi * (self.wavelengths1 - 400) / 100) + 1
        self.values2 = np.cos(np.pi * (self.wavelengths2 - 420) / 180) + 1
        self.values3 = 0.5 * np.exp(-(self.wavelengths3 - 450) ** 2 / 1000)

        # Create sensor filter
        self.filter_wavelengths = np.arange(380, 601, 5)
        self.filter_response = np.zeros((3, len(self.filter_wavelengths)))

        # Simple rectangular bands for testing
        band1_center = 440
        band2_center = 500
        band3_center = 560
        band_width = 30

        for i, center in enumerate([band1_center, band2_center, band3_center]):
            indices = np.where(
                (self.filter_wavelengths >= center - band_width / 2) &
                (self.filter_wavelengths <= center + band_width / 2)
            )[0]
            self.filter_response[i, indices] = 1.0

        self.sensor_filter = (self.filter_wavelengths, self.filter_response)

        # Create spectra list
        self.spectra_list = [
            (self.wavelengths1, self.values1),
            (self.wavelengths2, self.values2),
            (self.wavelengths3, self.values3)
        ]

    def test_prepare_spectral_inputs(self):
        """Test preparation of spectral inputs."""
        # Import the function to test
        from sambuca_core import prepare_spectral_inputs

        # Call the function
        wavelengths, processed_filter, masked_spectra = prepare_spectral_inputs(
            None, self.sensor_filter, self.spectra_list, truncate_filter=True
        )

        # Expected common wavelength range: 420-500 (inclusive)
        expected_wavelengths = np.arange(420, 501, 5)
        assert_array_equal(wavelengths, expected_wavelengths)

        # Check that the filter was truncated correctly
        filter_wavelengths, filter_response = processed_filter
        assert_array_equal(filter_wavelengths, expected_wavelengths)

        # The filter response should be a subset of the original
        start_idx = np.where(self.filter_wavelengths == 420)[0][0]
        end_idx = np.where(self.filter_wavelengths == 500)[0][0] + 1
        expected_response = self.filter_response[:, start_idx:end_idx]
        assert_array_equal(filter_response, expected_response)

        # Check that the spectral data was masked correctly
        self.assertEqual(len(masked_spectra), 3)

        # Each masked spectrum should have the common wavelength range
        for spectra in masked_spectra:
            assert_array_equal(spectra[0], expected_wavelengths)


if __name__ == '__main__':
    unittest.main()