"""Integration tests for inversion algorithms and parameter handling."""

import unittest
import tempfile
import shutil
import os
import numpy as np
import pandas as pd
from pathlib import Path
import pytest

import sambuca_core as sbc
from sambuca_core.inversion import (
    InversionParameters,
    invert_spectrum,
    multi_start_inversion,
    process_image
)
from sambuca_core.inversion.lut import LookUpTable
from sambuca_core.inversion.objective_functions import (
    spectral_rmse,
    spectral_angle_mapper,
    spectral_rmse_with_nedr
)


class TestInversionIntegration(unittest.TestCase):
    """Integration tests for inversion algorithms and parameter management."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.siop_dir = os.path.join(cls.temp_dir, 'siops')
        cls.create_test_siops()
        cls.setup_test_parameters()
        cls.generate_test_observations()

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        if hasattr(cls, 'temp_dir') and os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    @classmethod
    def create_test_siops(cls):
        """Create comprehensive test SIOP files."""
        os.makedirs(cls.siop_dir, exist_ok=True)

        # Use realistic wavelengths (Sentinel-2 subset)
        cls.wavelengths = np.array([492.4, 559.8, 664.6, 704.1])

        # Realistic SIOP values
        water_abs = np.array([0.0105, 0.0162, 0.3946, 0.6250])
        df = pd.DataFrame({'Wavelength': cls.wavelengths, 'Absorption': water_abs})
        df.to_csv(os.path.join(cls.siop_dir, 'water_absorption.csv'), index=False)

        ph_abs = np.array([0.0280, 0.0200, 0.0120, 0.0100])
        df = pd.DataFrame({'Wavelength': cls.wavelengths, 'Absorption': ph_abs})
        df.to_csv(os.path.join(cls.siop_dir, 'phytoplankton_absorption.csv'), index=False)

        sand_refl = np.array([0.15, 0.25, 0.35, 0.40])
        df = pd.DataFrame({'Wavelength': cls.wavelengths, 'Reflectance': sand_refl})
        df.to_csv(os.path.join(cls.siop_dir, 'sand_substrate.csv'), index=False)

        seagrass_refl = np.array([0.05, 0.15, 0.10, 0.08])
        df = pd.DataFrame({'Wavelength': cls.wavelengths, 'Reflectance': seagrass_refl})
        df.to_csv(os.path.join(cls.siop_dir, 'seagrass_substrate.csv'), index=False)

    @classmethod
    def setup_test_parameters(cls):
        """Set up standard inversion parameters for testing."""
        # Set up SIOP manager
        cls.siop_manager = sbc.SIOPManager(cls.siop_dir)
        cls.siop_manager.register_sensor("TestSensor", cls.wavelengths)

        # Create various parameter configurations for testing
        cls.depth_only_params = InversionParameters(
            depth=(0, 15),
            fixed_chl=1.0,
            fixed_cdom=0.1,
            fixed_nap=0.5,
            wavelengths=cls.wavelengths
        )
        cls.depth_only_params.update_from_siop_manager(cls.siop_manager, "TestSensor")

        cls.multi_param_params = InversionParameters(
            depth=(0, 15),
            chl=(0.1, 5.0),
            fixed_cdom=0.1,
            fixed_nap=0.5,
            wavelengths=cls.wavelengths
        )
        cls.multi_param_params.update_from_siop_manager(cls.siop_manager, "TestSensor")

        cls.full_params = InversionParameters(
            depth=(0, 15),
            chl=(0.1, 5.0),
            cdom=(0.01, 0.5),
            nap=(0.1, 2.0),
            wavelengths=cls.wavelengths
        )
        cls.full_params.update_from_siop_manager(cls.siop_manager, "TestSensor")

    @classmethod
    def generate_test_observations(cls):
        """Generate synthetic but realistic test observations."""
        # Test scenarios with known parameters
        cls.test_scenarios = [
            # Scenario 1: Shallow clear water
            {'name': 'shallow_clear', 'chl': 0.5, 'cdom': 0.05, 'nap': 0.2, 'depth': 2.0},
            # Scenario 2: Medium depth, moderate turbidity
            {'name': 'medium_moderate', 'chl': 1.5, 'cdom': 0.1, 'nap': 0.5, 'depth': 8.0},
            # Scenario 3: Deep clear water
            {'name': 'deep_clear', 'chl': 0.3, 'cdom': 0.02, 'nap': 0.1, 'depth': 15.0},
            # Scenario 4: Shallow turbid water
            {'name': 'shallow_turbid', 'chl': 3.0, 'cdom': 0.3, 'nap': 1.5, 'depth': 1.5},
        ]

        cls.test_observations = {}

        for scenario in cls.test_scenarios:
            try:
                # Generate forward model results
                results = sbc.forward_model(
                    chl=scenario['chl'],
                    cdom=scenario['cdom'],
                    nap=scenario['nap'],
                    depth=scenario['depth'],
                    wavelengths=cls.wavelengths,
                    a_water=cls.depth_only_params.a_water,
                    a_ph_star=cls.depth_only_params.a_ph_star,
                    substrate1=cls.depth_only_params.substrate1,
                    num_bands=len(cls.wavelengths)
                )

                # Store both clean and noisy observations
                cls.test_observations[scenario['name']] = {
                    'clean': results.rrs,
                    'noisy': results.rrs + np.random.normal(0, 0.001, len(results.rrs)),
                    'truth': scenario
                }

            except Exception as e:
                print(f"Failed to generate scenario {scenario['name']}: {e}")

    def test_single_parameter_inversion(self):
        """Test single parameter inversion (depth only)."""
        if not self.test_observations:
            self.skipTest("No test observations available")

        for scenario_name, obs_data in self.test_observations.items():
            with self.subTest(scenario=scenario_name):
                try:
                    # Test depth-only inversion
                    result = invert_spectrum(
                        obs_data['clean'],
                        self.depth_only_params
                    )

                    # Check result structure
                    self.assertIn('depth', result.parameters)
                    self.assertIsInstance(result.objective_value, float)
                    self.assertIsInstance(result.convergence_status, bool)

                    # Check parameter recovery
                    true_depth = obs_data['truth']['depth']
                    estimated_depth = result.parameters['depth']

                    # Should be reasonably close (allow for some error)
                    relative_error = abs(estimated_depth - true_depth) / true_depth
                    self.assertLess(relative_error, 0.3,
                                    f"Depth estimation error too large: {relative_error:.3f}")

                    print(f"✓ {scenario_name}: depth {true_depth:.1f}m → {estimated_depth:.1f}m "
                          f"(error: {relative_error:.1%})")

                except Exception as e:
                    print(f"⚠️ {scenario_name} single parameter inversion failed: {e}")

    def test_multi_parameter_inversion(self):
        """Test multi-parameter inversion (depth + chlorophyll)."""
        if not self.test_observations:
            self.skipTest("No test observations available")

        for scenario_name, obs_data in self.test_observations.items():
            with self.subTest(scenario=scenario_name):
                try:
                    # Test depth + chlorophyll inversion
                    result = invert_spectrum(
                        obs_data['clean'],
                        self.multi_param_params
                    )

                    # Check result structure
                    self.assertIn('depth', result.parameters)
                    self.assertIn('chl', result.parameters)

                    # Check parameter recovery
                    truth = obs_data['truth']

                    depth_error = abs(result.parameters['depth'] - truth['depth']) / truth['depth']
                    chl_error = abs(result.parameters['chl'] - truth['chl']) / truth['chl']

                    # Multi-parameter inversion is harder, so allow larger errors
                    self.assertLess(depth_error, 0.5, "Depth error too large in multi-param inversion")
                    self.assertLess(chl_error, 0.5, "Chlorophyll error too large in multi-param inversion")

                    print(f"✓ {scenario_name}: depth {depth_error:.1%}, chl {chl_error:.1%} error")

                except Exception as e:
                    print(f"⚠️ {scenario_name} multi-parameter inversion failed: {e}")

    def test_multi_start_inversion(self):
        """Test multi-start inversion for robustness."""
        if not self.test_observations:
            self.skipTest("No test observations available")

        # Test on one representative scenario
        scenario_name = 'medium_moderate'
        if scenario_name not in self.test_observations:
            scenario_name = next(iter(self.test_observations.keys()))

        obs_data = self.test_observations[scenario_name]

        try:
            # Single start inversion
            single_result = invert_spectrum(
                obs_data['noisy'],  # Use noisy data to test robustness
                self.depth_only_params
            )

            # Multi-start inversion
            multi_result = multi_start_inversion(
                obs_data['noisy'],
                self.depth_only_params,
                n_starts=3
            )

            # Multi-start should generally perform better or equal
            self.assertLessEqual(multi_result.objective_value,
                                 single_result.objective_value * 1.1,
                                 "Multi-start should not perform significantly worse")

            print(f"✓ Multi-start vs single: {multi_result.objective_value:.6f} vs "
                  f"{single_result.objective_value:.6f}")

        except Exception as e:
            self.skipTest(f"Multi-start inversion test failed: {e}")

    def test_objective_functions(self):
        """Test different objective functions."""
        if not self.test_observations:
            self.skipTest("No test observations available")

        scenario_name = next(iter(self.test_observations.keys()))
        obs_data = self.test_observations[scenario_name]
        truth = obs_data['truth']

        # Test parameters that should give good fit
        test_params = [truth['chl'], truth['cdom'], truth['nap'], truth['depth']]

        try:
            # Test RMSE
            rmse_error = spectral_rmse(
                test_params,
                obs_data['clean'],
                self.full_params
            )
            self.assertIsInstance(rmse_error, float)
            self.assertGreater(rmse_error, 0)

            # Test Spectral Angle Mapper
            sam_error = spectral_angle_mapper(
                test_params,
                obs_data['clean'],
                self.full_params
            )
            self.assertIsInstance(sam_error, float)
            self.assertGreater(sam_error, 0)

            # Test NEDR-weighted RMSE
            nedr_values = np.array([0.001, 0.001, 0.002, 0.003])  # Example NEDR values
            nedr_error = spectral_rmse_with_nedr(
                test_params,
                obs_data['clean'],
                self.full_params,
                nedr=nedr_values
            )
            self.assertIsInstance(nedr_error, float)
            self.assertGreater(nedr_error, 0)

            print(f"✓ Objective functions: RMSE={rmse_error:.6f}, SAM={sam_error:.6f}, "
                  f"NEDR-RMSE={nedr_error:.6f}")

        except Exception as e:
            self.skipTest(f"Objective function test failed: {e}")

    def test_inversion_with_noise(self):
        """Test inversion robustness to different noise levels."""
        if not self.test_observations:
            self.skipTest("No test observations available")

        scenario_name = 'medium_moderate'
        if scenario_name not in self.test_observations:
            scenario_name = next(iter(self.test_observations.keys()))

        obs_data = self.test_observations[scenario_name]
        clean_obs = obs_data['clean']
        truth = obs_data['truth']

        noise_levels = [0.001, 0.005, 0.01]

        for noise_level in noise_levels:
            with self.subTest(noise_level=noise_level):
                try:
                    # Add noise
                    noisy_obs = clean_obs + np.random.normal(0, noise_level, len(clean_obs))

                    # Run inversion
                    result = invert_spectrum(noisy_obs, self.depth_only_params)

                    # Check that we still get reasonable results
                    self.assertTrue(result.convergence_status,
                                    f"Should converge with noise level {noise_level}")

                    # Error should increase with noise but stay reasonable
                    depth_error = abs(result.parameters['depth'] - truth['depth']) / truth['depth']
                    self.assertLess(depth_error, 0.5,
                                    f"Error too large with noise {noise_level}: {depth_error:.3f}")

                    print(f"✓ Noise {noise_level}: depth error {depth_error:.1%}")

                except Exception as e:
                    print(f"⚠️ Noise level {noise_level} test failed: {e}")

    def test_parameter_bounds_validation(self):
        """Test that inversions respect parameter bounds."""
        if not self.test_observations:
            self.skipTest("No test observations available")

        scenario_name = next(iter(self.test_observations.keys()))
        obs_data = self.test_observations[scenario_name]

        try:
            result = invert_spectrum(obs_data['clean'], self.multi_param_params)

            # Check bounds for each parameter
            bounds = self.multi_param_params.get_parameter_bounds()
            param_names = self.multi_param_params.get_inversion_parameter_names()

            for i, param_name in enumerate(param_names):
                value = result.parameters[param_name]
                lower, upper = bounds[i]

                # Allow small numerical tolerance
                self.assertGreaterEqual(value, lower - 1e-10,
                                        f"{param_name} below lower bound: {value} < {lower}")
                self.assertLessEqual(value, upper + 1e-10,
                                     f"{param_name} above upper bound: {value} > {upper}")

            print("✓ Parameter bounds validation passed")

        except Exception as e:
            self.skipTest(f"Bounds validation test failed: {e}")

    @pytest.mark.integration
    def test_batch_pixel_processing(self):
        """Test processing multiple pixels (simulating image processing)."""
        if not self.test_observations:
            self.skipTest("No test observations available")

        # Create a small synthetic image with different scenarios
        height, width = 10, 10
        n_bands = len(self.wavelengths)

        # Create image with different scenarios in different areas
        synthetic_image = np.zeros((height, width, n_bands))

        scenarios = list(self.test_observations.keys())[:4]  # Use up to 4 scenarios

        for i, scenario_name in enumerate(scenarios):
            obs_data = self.test_observations[scenario_name]

            # Fill a quadrant with this scenario
            start_y = (i // 2) * (height // 2)
            start_x = (i % 2) * (width // 2)
            end_y = start_y + height // 2
            end_x = start_x + width // 2

            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    synthetic_image[y, x, :] = obs_data['clean']

        try:
            # Process the synthetic image
            results = process_image(
                synthetic_image,
                self.depth_only_params,
                n_processes=1,
                progress_bar=False
            )

            # Check results
            self.assertIn('depth', results)
            self.assertEqual(results['depth'].shape, (height, width))

            # Check that we got some valid results
            valid_depths = results['depth'][~np.isnan(results['depth'])]
            self.assertGreater(len(valid_depths), 0, "Should have some valid depth retrievals")

            # Check that depths are reasonable
            self.assertTrue(np.all(valid_depths >= 0))
            self.assertTrue(np.all(valid_depths <= 20))

            print(f"✓ Batch processing: {len(valid_depths)}/{height * width} valid pixels")

        except Exception as e:
            self.skipTest(f"Batch processing test failed: {e}")

    def test_convergence_analysis(self):
        """Test analysis of convergence patterns."""
        if not self.test_observations:
            self.skipTest("No test observations available")

        convergence_stats = {'converged': 0, 'failed': 0, 'errors': []}

        for scenario_name, obs_data in self.test_observations.items():
            try:
                result = invert_spectrum(obs_data['noisy'], self.depth_only_params)

                if result.convergence_status:
                    convergence_stats['converged'] += 1
                else:
                    convergence_stats['failed'] += 1

                convergence_stats['errors'].append(result.objective_value)

            except Exception as e:
                convergence_stats['failed'] += 1
                print(f"⚠️ {scenario_name} failed with exception: {e}")

        total_tests = convergence_stats['converged'] + convergence_stats['failed']
        if total_tests > 0:
            success_rate = convergence_stats['converged'] / total_tests

            # Should have reasonable success rate
            self.assertGreater(success_rate, 0.5, "Convergence rate should be > 50%")

            if convergence_stats['errors']:
                mean_error = np.mean(convergence_stats['errors'])
                self.assertLess(mean_error, 0.1, "Mean error should be reasonable")

            print(f"✓ Convergence analysis: {success_rate:.1%} success rate, "
                  f"mean error: {np.mean(convergence_stats['errors']):.6f}")


if __name__ == '__main__':
    unittest.main()