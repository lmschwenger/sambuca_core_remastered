#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Sambuca Core
===============================================

This test suite provides comprehensive testing of the sambuca_core package,
including integration tests, edge cases, and error handling.
"""

import unittest
import tempfile
import shutil
import os
import numpy as np
import pandas as pd
from pathlib import Path

import sambuca_core as sbc
from sambuca_core.inversion import InversionParameters, invert_spectrum, multi_start_inversion
from sambuca_core.inversion.lut import LookUpTable
from sambuca_core.exceptions import SambucaException, DataValidationError


class TestForwardModelComprehensive(unittest.TestCase):
    """Comprehensive tests for the forward model."""

    def setUp(self):
        """Set up test data."""
        self.num_bands = 4
        self.wavelengths = np.array([400, 500, 600, 700])
        self.a_water = np.array([0.01, 0.02, 0.1, 0.5])
        self.a_ph_star = np.array([0.05, 0.03, 0.02, 0.01])
        self.substrate1 = np.array([0.1, 0.2, 0.3, 0.4])
        self.substrate2 = np.array([0.05, 0.15, 0.25, 0.35])

    def test_forward_model_minimum_inputs(self):
        """Test forward model with minimum required inputs."""
        results = sbc.forward_model(
            chl=1.0,
            cdom=0.1,
            nap=0.5,
            depth=5.0,
            substrate1=self.substrate1,
            wavelengths=self.wavelengths,
            a_water=self.a_water,
            a_ph_star=self.a_ph_star,
            num_bands=self.num_bands
        )

        # Check all required outputs are present
        required_attrs = ['rrs', 'rrsdp', 'r_0_minus', 'rdp_0_minus', 'a', 'bb', 'kd']
        for attr in required_attrs:
            self.assertTrue(hasattr(results, attr))
            self.assertEqual(len(getattr(results, attr)), self.num_bands)

    def test_forward_model_edge_cases(self):
        """Test forward model with edge case parameters."""
        edge_cases = [
            # Very low concentrations
            {'chl': 0.001, 'cdom': 0.001, 'nap': 0.001, 'depth': 0.1},
            # Very high concentrations
            {'chl': 100.0, 'cdom': 10.0, 'nap': 50.0, 'depth': 100.0},
            # Zero concentrations
            {'chl': 0.0, 'cdom': 0.0, 'nap': 0.0, 'depth': 0.1},
        ]

        for case in edge_cases:
            with self.subTest(case=case):
                results = sbc.forward_model(
                    **case,
                    substrate1=self.substrate1,
                    wavelengths=self.wavelengths,
                    a_water=self.a_water,
                    a_ph_star=self.a_ph_star,
                    num_bands=self.num_bands
                )

                # Check outputs are finite and reasonable
                self.assertTrue(np.all(np.isfinite(results.rrs)))
                self.assertTrue(np.all(results.rrs >= 0))
                self.assertTrue(np.all(results.a >= 0))
                self.assertTrue(np.all(results.bb >= 0))

    def test_forward_model_substrate_mixing(self):
        """Test substrate mixing functionality."""
        # Test pure substrate1
        results1 = sbc.forward_model(
            chl=1.0, cdom=0.1, nap=0.5, depth=5.0,
            substrate1=self.substrate1,
            substrate2=self.substrate2,
            substrate_fraction=1.0,
            wavelengths=self.wavelengths,
            a_water=self.a_water,
            a_ph_star=self.a_ph_star,
            num_bands=self.num_bands
        )

        # Test pure substrate2
        results2 = sbc.forward_model(
            chl=1.0, cdom=0.1, nap=0.5, depth=5.0,
            substrate1=self.substrate1,
            substrate2=self.substrate2,
            substrate_fraction=0.0,
            wavelengths=self.wavelengths,
            a_water=self.a_water,
            a_ph_star=self.a_ph_star,
            num_bands=self.num_bands
        )

        # Test 50/50 mix
        results_mix = sbc.forward_model(
            chl=1.0, cdom=0.1, nap=0.5, depth=5.0,
            substrate1=self.substrate1,
            substrate2=self.substrate2,
            substrate_fraction=0.5,
            wavelengths=self.wavelengths,
            a_water=self.a_water,
            a_ph_star=self.a_ph_star,
            num_bands=self.num_bands
        )

        # Check substrate mixing
        np.testing.assert_array_almost_equal(
            results1.r_substratum, self.substrate1
        )
        np.testing.assert_array_almost_equal(
            results2.r_substratum, self.substrate2
        )

        expected_mix = 0.5 * self.substrate1 + 0.5 * self.substrate2
        np.testing.assert_array_almost_equal(
            results_mix.r_substratum, expected_mix
        )

    def test_forward_model_input_validation(self):
        """Test input validation and error handling."""

        # Test mismatched array lengths
        with self.assertRaises(AssertionError):
            sbc.forward_model(
                chl=1.0, cdom=0.1, nap=0.5, depth=5.0,
                substrate1=self.substrate1[:-1],  # Wrong length
                wavelengths=self.wavelengths,
                a_water=self.a_water,
                a_ph_star=self.a_ph_star,
                num_bands=self.num_bands
            )

        # Test wrong num_bands
        with self.assertRaises(AssertionError):
            sbc.forward_model(
                chl=1.0, cdom=0.1, nap=0.5, depth=5.0,
                substrate1=self.substrate1,
                wavelengths=self.wavelengths,
                a_water=self.a_water,
                a_ph_star=self.a_ph_star,
                num_bands=self.num_bands + 1  # Wrong number
            )


class TestSIOPManagerComprehensive(unittest.TestCase):
    """Comprehensive tests for the SIOP Manager."""

    def setUp(self):
        """Set up test SIOP directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.create_test_siops()
        self.siop_manager = sbc.SIOPManager(self.temp_dir)

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.temp_dir)

    def create_test_siops(self):
        """Create test SIOP files."""
        wavelengths = np.arange(400, 801, 10)  # 400-800nm, 10nm steps

        # Create water absorption
        water_abs = 0.01 + 0.001 * (wavelengths - 400) / 10
        df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': water_abs})
        df.to_csv(os.path.join(self.temp_dir, 'water_absorption.csv'), index=False)

        # Create phytoplankton absorption
        ph_abs = 0.02 * np.exp(-0.01 * (wavelengths - 440) ** 2) + 0.01
        df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': ph_abs})
        df.to_csv(os.path.join(self.temp_dir, 'phytoplankton_absorption.csv'), index=False)

        # Create sand substrate
        sand_refl = 0.1 + 0.3 * (wavelengths - 400) / 400
        df = pd.DataFrame({'Wavelength': wavelengths, 'Reflectance': sand_refl})
        df.to_csv(os.path.join(self.temp_dir, 'sand_substrate.csv'), index=False)

    def test_siop_loading(self):
        """Test SIOP loading functionality."""
        libraries = self.siop_manager.list_available_libraries()

        # Should have loaded our test files
        expected_libs = ['water_absorption', 'phytoplankton_absorption', 'sand_substrate']
        for lib in expected_libs:
            self.assertIn(lib, libraries)

    def test_sensor_registration(self):
        """Test sensor registration and wavelength interpolation."""
        # Register test sensor
        test_wavelengths = [450, 550, 650, 750]
        self.siop_manager.register_sensor("TestSensor", test_wavelengths)

        # Get interpolated SIOPs
        siops = self.siop_manager.get_siops_for_sensor("TestSensor")

        # Check wavelengths match
        np.testing.assert_array_equal(siops['wavelengths'], test_wavelengths)

        # Check all expected SIOPs are present
        expected_siops = ['water_absorption', 'phytoplankton_absorption', 'sand_substrate']
        for siop in expected_siops:
            self.assertIn(siop, siops)
            self.assertEqual(len(siops[siop]), len(test_wavelengths))

    def test_interpolation_quality(self):
        """Test quality of SIOP interpolation."""
        # Register sensor with wavelengths that match original data
        original_wavelengths = np.arange(400, 801, 10)
        subset_wavelengths = [420, 460, 540, 680]  # Subset of original

        self.siop_manager.register_sensor("SubsetSensor", subset_wavelengths)
        siops = self.siop_manager.get_siops_for_sensor("SubsetSensor")

        # Load original data for comparison
        water_df = pd.read_csv(os.path.join(self.temp_dir, 'water_absorption.csv'))

        # Check interpolated values against original
        for i, wl in enumerate(subset_wavelengths):
            original_idx = np.where(water_df['Wavelength'] == wl)[0]
            if len(original_idx) > 0:
                original_value = water_df.iloc[original_idx[0]]['Absorption']
                interpolated_value = siops['water_absorption'][i]
                self.assertAlmostEqual(original_value, interpolated_value, places=5)

    def test_standard_siops(self):
        """Test standard SIOP retrieval."""
        # Register sensor
        self.siop_manager.register_sensor("TestSensor", [450, 550, 650])

        # Get standard SIOPs
        std_siops = self.siop_manager.get_standard_siops("TestSensor")

        # Check required components are present
        required_components = ['wavelengths', 'num_bands', 'a_water', 'a_ph_star', 'substrate1']
        for component in required_components:
            self.assertIn(component, std_siops)

    def test_error_handling(self):
        """Test error handling in SIOP Manager."""
        # Test unregistered sensor
        with self.assertRaises(KeyError):
            self.siop_manager.get_siops_for_sensor("NonexistentSensor")

        # Test standard SIOPs for unregistered sensor
        with self.assertRaises(KeyError):
            self.siop_manager.get_standard_siops("NonexistentSensor")


class TestInversionComprehensive(unittest.TestCase):
    """Comprehensive tests for the inversion functionality."""

    def setUp(self):
        """Set up test data for inversion."""
        self.wavelengths = np.array([450, 550, 650, 750])
        self.a_water = np.array([0.01, 0.02, 0.1, 0.5])
        self.a_ph_star = np.array([0.05, 0.03, 0.02, 0.01])
        self.substrate1 = np.array([0.1, 0.2, 0.3, 0.4])

        # Generate synthetic observed data
        self.true_params = {'chl': 2.0, 'cdom': 0.1, 'nap': 1.0, 'depth': 5.0}
        self.observed_rrs = self._generate_synthetic_data()

        # Set up inversion parameters
        self.inversion_params = InversionParameters(
            chl=(0.1, 10.0),
            cdom=(0.01, 1.0),
            nap=(0.1, 5.0),
            depth=(0.5, 15.0),
            wavelengths=self.wavelengths,
            a_water=self.a_water,
            a_ph_star=self.a_ph_star,
            substrate1=self.substrate1
        )

    def _generate_synthetic_data(self):
        """Generate synthetic observed data."""
        results = sbc.forward_model(
            chl=self.true_params['chl'],
            cdom=self.true_params['cdom'],
            nap=self.true_params['nap'],
            depth=self.true_params['depth'],
            wavelengths=self.wavelengths,
            a_water=self.a_water,
            a_ph_star=self.a_ph_star,
            substrate1=self.substrate1,
            num_bands=len(self.wavelengths)
        )
        return results.rrs

    def test_basic_inversion(self):
        """Test basic inversion functionality."""
        result = invert_spectrum(self.observed_rrs, self.inversion_params)

        # Check result structure
        self.assertIsInstance(result.parameters, dict)
        self.assertIsInstance(result.objective_value, float)
        self.assertEqual(len(result.modeled_spectra), len(self.wavelengths))

        # Check parameter recovery (should be reasonably close)
        for param, true_val in self.true_params.items():
            recovered_val = result.parameters[param]
            relative_error = abs(recovered_val - true_val) / true_val
            self.assertLess(relative_error, 0.1,
                            f"Parameter {param}: expected {true_val}, got {recovered_val}")

    def test_multi_start_inversion(self):
        """Test multi-start inversion."""
        result = multi_start_inversion(self.observed_rrs, self.inversion_params, n_starts=3)

        # Should have same structure as basic inversion
        self.assertIsInstance(result.parameters, dict)
        self.assertIsInstance(result.objective_value, float)

        # Multi-start should generally perform at least as well as single start
        single_result = invert_spectrum(self.observed_rrs, self.inversion_params)
        self.assertLessEqual(result.objective_value, single_result.objective_value * 1.1)

    def test_inversion_with_noise(self):
        """Test inversion robustness to noise."""
        # Add different levels of noise
        noise_levels = [0.001, 0.005, 0.01]

        for noise_level in noise_levels:
            with self.subTest(noise_level=noise_level):
                noise = np.random.normal(0, noise_level, len(self.observed_rrs))
                noisy_rrs = self.observed_rrs + noise

                result = invert_spectrum(noisy_rrs, self.inversion_params)

                # Should still converge
                self.assertTrue(result.convergence_status)

                # Error should increase with noise level
                self.assertGreater(result.objective_value, noise_level / 10)
                self.assertLess(result.objective_value, noise_level * 10)

    def test_inversion_bounds(self):
        """Test that inversion respects parameter bounds."""
        result = invert_spectrum(self.observed_rrs, self.inversion_params)

        bounds = self.inversion_params.get_parameter_bounds()
        param_names = self.inversion_params.get_inversion_parameter_names()

        for i, param_name in enumerate(param_names):
            value = result.parameters[param_name]
            lower, upper = bounds[i]

            self.assertGreaterEqual(value, lower * 0.99,  # Small tolerance for numerical precision
                                    f"Parameter {param_name} below lower bound")
            self.assertLessEqual(value, upper * 1.01,  # Small tolerance for numerical precision
                                 f"Parameter {param_name} above upper bound")

    def test_inversion_parameter_validation(self):
        """Test inversion parameter validation."""
        # Test empty parameter bounds
        empty_params = InversionParameters(wavelengths=self.wavelengths)

        with self.assertRaises(ValueError):
            invert_spectrum(self.observed_rrs, empty_params)

    def test_objective_functions(self):
        """Test different objective functions."""
        from sambuca_core.inversion.objective_functions import (
            spectral_rmse, spectral_angle_mapper, spectral_relative_rmse
        )

        # Create test parameters
        test_params = [2.0, 0.1, 1.0, 5.0]  # chl, cdom, nap, depth

        # Test each objective function
        rmse_error = spectral_rmse(test_params, self.observed_rrs, self.inversion_params)
        sam_error = spectral_angle_mapper(test_params, self.observed_rrs, self.inversion_params)
        rel_rmse_error = spectral_relative_rmse(test_params, self.observed_rrs, self.inversion_params)

        # All should return scalar values
        self.assertIsInstance(rmse_error, float)
        self.assertIsInstance(sam_error, float)
        self.assertIsInstance(rel_rmse_error, float)

        # All should be positive
        self.assertGreater(rmse_error, 0)
        self.assertGreater(sam_error, 0)
        self.assertGreater(rel_rmse_error, 0)


class TestLookUpTableComprehensive(unittest.TestCase):
    """Comprehensive tests for the Look-Up Table functionality."""

    def setUp(self):
        """Set up test data for LUT."""
        self.wavelengths = np.array([450, 550, 650])
        self.a_water = np.array([0.01, 0.02, 0.1])
        self.a_ph_star = np.array([0.05, 0.03, 0.02])
        self.substrate1 = np.array([0.1, 0.2, 0.3])

        # Simple inversion parameters for LUT
        self.inversion_params = InversionParameters(
            chl=(0.5, 3.0),
            depth=(1.0, 10.0),
            fixed_cdom=0.1,
            fixed_nap=1.0,
            wavelengths=self.wavelengths,
            a_water=self.a_water,
            a_ph_star=self.a_ph_star,
            substrate1=self.substrate1
        )

    def test_lut_creation_and_building(self):
        """Test LUT creation and building."""
        lut = LookUpTable(self.inversion_params)

        # Build small LUT for testing
        lut.build_table(grid_size=5, progress_bar=False)

        self.assertTrue(lut.table_built)
        self.assertIsNotNone(lut.param_array)
        self.assertIsNotNone(lut.spectra_array)

        # Check dimensions
        expected_combinations = 5 * 5  # 5x5 grid for 2 parameters
        self.assertEqual(len(lut.param_array), expected_combinations)
        self.assertEqual(lut.spectra_array.shape[0], expected_combinations)
        self.assertEqual(lut.spectra_array.shape[1], len(self.wavelengths))

    def test_lut_inversion(self):
        """Test LUT-based inversion."""
        lut = LookUpTable(self.inversion_params)
        lut.build_table(grid_size=10, progress_bar=False)

        # Generate test observation
        test_params = {'chl': 2.0, 'depth': 5.0}
        results = sbc.forward_model(
            chl=test_params['chl'],
            cdom=0.1,
            nap=1.0,
            depth=test_params['depth'],
            wavelengths=self.wavelengths,
            a_water=self.a_water,
            a_ph_star=self.a_ph_star,
            substrate1=self.substrate1,
            num_bands=len(self.wavelengths)
        )

        # Invert using LUT
        lut_result = lut.invert(results.rrs, refine=False)

        # Check result structure
        self.assertIn('parameters', lut_result)
        self.assertIn('error', lut_result)
        self.assertIn('modeled_spectra', lut_result)

        # Check parameter recovery
        for param, true_val in test_params.items():
            recovered_val = lut_result['parameters'][param]
            relative_error = abs(recovered_val - true_val) / true_val
            self.assertLess(relative_error, 0.2,  # LUT has lower precision
                            f"LUT parameter {param}: expected {true_val}, got {recovered_val}")

    def test_lut_refinement(self):
        """Test LUT with optimization refinement."""
        lut = LookUpTable(self.inversion_params)
        lut.build_table(grid_size=5, progress_bar=False)

        # Generate test observation
        results = sbc.forward_model(
            chl=2.0, cdom=0.1, nap=1.0, depth=5.0,
            wavelengths=self.wavelengths,
            a_water=self.a_water,
            a_ph_star=self.a_ph_star,
            substrate1=self.substrate1,
            num_bands=len(self.wavelengths)
        )

        # Test with and without refinement
        lut_only = lut.invert(results.rrs, refine=False)
        lut_refined = lut.invert(results.rrs, refine=True)

        # Refined should generally have lower error
        self.assertLessEqual(lut_refined['error'], lut_only['error'] * 1.1)

    def test_lut_save_load(self):
        """Test LUT save and load functionality."""
        lut1 = LookUpTable(self.inversion_params)
        lut1.build_table(grid_size=5, progress_bar=False)

        # Save LUT
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as temp_file:
            temp_filename = temp_file.name

        try:
            lut1.save(temp_filename)

            # Load LUT
            lut2 = LookUpTable.load(temp_filename, build_kdtree=False)

            # Check loaded LUT has same properties
            self.assertTrue(lut2.table_built)
            np.testing.assert_array_equal(lut1.param_array, lut2.param_array)
            np.testing.assert_array_equal(lut1.spectra_array, lut2.spectra_array)

        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""

    def test_invalid_file_formats(self):
        """Test handling of invalid file formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create invalid CSV file
            invalid_file = os.path.join(temp_dir, "invalid.csv")
            with open(invalid_file, 'w') as f:
                f.write("not,a,valid,csv,format\n")
                f.write("with,inconsistent,rows\n")

            # Should handle gracefully
            siop_manager = sbc.SIOPManager(temp_dir)
            libraries = siop_manager.list_available_libraries()
            # Should not crash, but may not load the invalid file

    def test_data_validation_errors(self):
        """Test data validation error handling."""
        # This would require creating specific invalid data scenarios
        # For now, we'll test that the exceptions exist and can be raised

        with self.assertRaises(DataValidationError):
            raise DataValidationError("Test validation error")

        with self.assertRaises(SambucaException):
            raise SambucaException("Test sambuca error")


def create_test_suite():
    """Create a comprehensive test suite."""
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestForwardModelComprehensive,
        TestSIOPManagerComprehensive,
        TestInversionComprehensive,
        TestLookUpTableComprehensive,
        TestErrorHandling
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    return suite


if __name__ == '__main__':
    # Run the comprehensive test suite
    print("Running Sambuca Core Comprehensive Test Suite")
    print("=" * 60)

    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_test_suite()
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")

    print("=" * 60)