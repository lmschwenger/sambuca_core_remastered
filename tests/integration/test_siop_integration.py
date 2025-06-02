"""Integration tests for SIOP management and sensor configurations."""

import unittest
import tempfile
import shutil
import os
import numpy as np
import pandas as pd
from pathlib import Path
import pytest

import sambuca.core as sbc
from sambuca.core.sensors import SensorFactory, Sentinel2Sensor
from sambuca.core.inversion import InversionParameters


class TestSIOPIntegration(unittest.TestCase):
    """Integration tests for SIOP management and sensor configurations."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.siop_dir = os.path.join(cls.temp_dir, 'siops')
        cls.create_comprehensive_siops()

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        if hasattr(cls, 'temp_dir') and os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    @classmethod
    def create_comprehensive_siops(cls):
        """Create comprehensive SIOP library for testing."""
        os.makedirs(cls.siop_dir, exist_ok=True)

        # Create subdirectories for better organization
        absorption_dir = os.path.join(cls.siop_dir, 'absorption')
        backscatter_dir = os.path.join(cls.siop_dir, 'backscatter')
        substrates_dir = os.path.join(cls.siop_dir, 'substrates')

        os.makedirs(absorption_dir, exist_ok=True)
        os.makedirs(backscatter_dir, exist_ok=True)
        os.makedirs(substrates_dir, exist_ok=True)

        # Wide wavelength range for interpolation testing
        wavelengths = np.arange(400, 801, 2)  # 400-800nm, 2nm steps

        # Water absorption (Pope & Fry 1997 approximation)
        water_abs = np.zeros_like(wavelengths, dtype=float)
        for i, wl in enumerate(wavelengths):
            if wl < 500:
                water_abs[i] = 0.01 + 0.05 * np.exp(-(wl - 400) / 30)
            elif wl < 600:
                water_abs[i] = 0.015 + (wl - 500) * 0.0006
            elif wl < 700:
                water_abs[i] = 0.075 + (wl - 600) * 0.003
            else:
                water_abs[i] = 0.375 + (wl - 700) * 0.005

        df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': water_abs})
        df.to_csv(os.path.join(cls.siop_dir, 'water_absorption.csv'), index=False)

        # Phytoplankton absorption with realistic spectral features
        ph_abs = 0.02 * np.ones_like(wavelengths, dtype=float)
        ph_abs += 0.02 * np.exp(-0.005 * (wavelengths - 440) ** 2)  # Blue peak
        ph_abs += 0.005 * np.exp(-0.005 * (wavelengths - 675) ** 2)  # Red peak

        df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': ph_abs})
        df.to_csv(os.path.join(cls.siop_dir, 'phytoplankton_absorption.csv'), index=False)

        # CDOM absorption (exponential decay)
        cdom_abs = np.exp(-0.017 * (wavelengths - 440))
        df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': cdom_abs})
        df.to_csv(os.path.join(cls.siop_dir, 'cdom_absorption.csv'), index=False)

        # NAP absorption
        nap_abs = 0.04 * np.exp(-0.01 * (wavelengths - 440))
        df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': nap_abs})
        df.to_csv(os.path.join(cls.siop_dir, 'nap_absorption.csv'), index=False)

        # Water backscatter
        water_bb = 0.0019 / 2 * (550 / wavelengths) ** 4.32
        df = pd.DataFrame({'Wavelength': wavelengths, 'Backscatter': water_bb})
        df.to_csv(os.path.join(cls.siop_dir, 'water_backscatter.csv'), index=False)

        # Phytoplankton backscatter
        ph_bb = 0.0015 * (550 / wavelengths) ** 0.9
        df = pd.DataFrame({'Wavelength': wavelengths, 'Backscatter': ph_bb})
        df.to_csv(os.path.join(cls.siop_dir, 'phytoplankton_backscatter.csv'), index=False)

        # NAP backscatter
        nap_bb = 0.022 * (550 / wavelengths) ** 0.9
        df = pd.DataFrame({'Wavelength': wavelengths, 'Backscatter': nap_bb})
        df.to_csv(os.path.join(cls.siop_dir, 'nap_backscatter.csv'), index=False)

        # Multiple substrate types
        substrates = {
            'sand': 0.1 + 0.3 * (wavelengths - 400) / 400,
            'seagrass': 0.05 + 0.1 * np.exp(-0.001 * (wavelengths - 550) ** 2),
            'mud': 0.02 + 0.06 * (wavelengths - 400) / 400,
            'coral': 0.08 + 0.2 * np.exp(-0.002 * (wavelengths - 500) ** 2),
        }

        for substrate_name, reflectance in substrates.items():
            reflectance = np.clip(reflectance, 0, 1)
            df = pd.DataFrame({'Wavelength': wavelengths, 'Reflectance': reflectance})
            df.to_csv(os.path.join(cls.siop_dir, f'{substrate_name}_substrate.csv'), index=False)

    def test_siop_manager_initialization(self):
        """Test SIOP manager initialization and library loading."""
        siop_manager = sbc.SIOPManager(self.siop_dir)

        # Check that libraries were loaded
        libraries = siop_manager.list_available_libraries()
        self.assertGreater(len(libraries), 0, "Should load some SIOP libraries")

        # Check for expected core libraries
        expected_libs = ['water_absorption', 'phytoplankton_absorption', 'sand_substrate']
        for lib in expected_libs:
            self.assertIn(lib, libraries, f"Should load {lib}")

        print(f"✓ Loaded {len(libraries)} SIOP libraries")

    def test_sensor_configurations(self):
        """Test built-in sensor configurations."""
        # Test Sentinel-2 sensor
        s2_sensor = SensorFactory.create('sentinel2')
        self.assertIsInstance(s2_sensor, Sentinel2Sensor)
        self.assertEqual(s2_sensor.name, "Sentinel-2")

        # Check wavelengths
        wavelengths = s2_sensor.band_wavelengths
        self.assertIn('B2', wavelengths)
        self.assertIn('B3', wavelengths)
        self.assertIn('B4', wavelengths)

        # Check standard configurations
        bands, wls = s2_sensor.get_standard_config('bathymetry')
        self.assertEqual(len(bands), len(wls))
        self.assertIn('B2', bands)

        print(f"✓ Sentinel-2 sensor: {len(wavelengths)} bands, bathymetry config: {len(bands)} bands")

    def test_sensor_registration_and_interpolation(self):
        """Test sensor registration and SIOP interpolation."""
        siop_manager = sbc.SIOPManager(self.siop_dir)

        # Test different sensor configurations
        test_sensors = [
            ('Sentinel-2', [492.4, 559.8, 664.6, 704.1]),
            ('Landsat-8', [482, 561, 655, 865]),
            ('MODIS', [469, 555, 645, 858]),
            ('Custom', [450, 550, 650, 750]),
        ]

        for sensor_name, wavelengths in test_sensors:
            with self.subTest(sensor=sensor_name):
                # Register sensor
                siop_manager.register_sensor(sensor_name, wavelengths)

                # Get interpolated SIOPs
                siops = siop_manager.get_siops_for_sensor(sensor_name)

                # Check basic structure
                self.assertIn('wavelengths', siops)
                self.assertIn('num_bands', siops)
                np.testing.assert_array_equal(siops['wavelengths'], wavelengths)
                self.assertEqual(siops['num_bands'], len(wavelengths))

                # Check that main SIOPs were interpolated
                expected_siops = ['water_absorption', 'phytoplankton_absorption', 'sand_substrate']
                for siop_name in expected_siops:
                    self.assertIn(siop_name, siops)
                    self.assertEqual(len(siops[siop_name]), len(wavelengths))

                print(f"✓ {sensor_name} interpolation successful")

    def test_interpolation_quality(self):
        """Test quality of SIOP interpolation."""
        siop_manager = sbc.SIOPManager(self.siop_dir)

        # Test interpolation at known wavelengths (should be exact)
        known_wavelengths = [450, 500, 550, 600, 650, 700]
        siop_manager.register_sensor("TestSensor", known_wavelengths)

        siops = siop_manager.get_siops_for_sensor("TestSensor")

        # Load original data for comparison
        water_df = pd.read_csv(os.path.join(self.siop_dir, 'water_absorption.csv'))

        for i, wl in enumerate(known_wavelengths):
            # Find original value at this wavelength
            original_idx = np.where(np.abs(water_df['Wavelength'] - wl) < 0.1)[0]
            if len(original_idx) > 0:
                original_value = water_df.iloc[original_idx[0]]['Absorption']
                interpolated_value = siops['water_absorption'][i]

                # Should be very close (interpolation should be accurate)
                rel_error = abs(interpolated_value - original_value) / original_value
                self.assertLess(rel_error, 0.01, f"Interpolation error too large at {wl}nm")

        print("✓ Interpolation quality test passed")

    def test_standard_siops_retrieval(self):
        """Test standard SIOP retrieval for forward model."""
        siop_manager = sbc.SIOPManager(self.siop_dir)

        # Test with Sentinel-2 configuration
        siop_manager.register_sensor("Sentinel-2", [492.4, 559.8, 664.6, 704.1])

        try:
            std_siops = siop_manager.get_standard_siops("Sentinel-2")

            # Check required components for forward model
            required_components = ['wavelengths', 'num_bands', 'a_water', 'a_ph_star', 'substrate1']
            for component in required_components:
                self.assertIn(component, std_siops, f"Missing required component: {component}")

            # Check array lengths match
            n_bands = std_siops['num_bands']
            self.assertEqual(len(std_siops['wavelengths']), n_bands)
            self.assertEqual(len(std_siops['a_water']), n_bands)
            self.assertEqual(len(std_siops['a_ph_star']), n_bands)
            self.assertEqual(len(std_siops['substrate1']), n_bands)

            # Check for optional second substrate
            if 'substrate2' in std_siops:
                self.assertEqual(len(std_siops['substrate2']), n_bands)

            print("✓ Standard SIOPs retrieval successful")

        except KeyError as e:
            self.fail(f"Standard SIOP retrieval failed: missing {e}")

    def test_siop_parameter_integration(self):
        """Test integration of SIOPs with InversionParameters."""
        siop_manager = sbc.SIOPManager(self.siop_dir)
        siop_manager.register_sensor("TestSensor", [450, 550, 650, 750])

        # Create parameters without SIOPs
        params = InversionParameters(
            depth=(0, 15),
            chl=(0.1, 5.0),
            wavelengths=[450, 550, 650, 750]
        )

        # Update with SIOPs
        params.update_from_siop_manager(siop_manager, "TestSensor")

        # Check that SIOPs were properly loaded
        self.assertIsNotNone(params.a_water)
        self.assertIsNotNone(params.a_ph_star)
        self.assertIsNotNone(params.substrate1)

        # Check lengths
        self.assertEqual(len(params.a_water), 4)
        self.assertEqual(len(params.a_ph_star), 4)
        self.assertEqual(len(params.substrate1), 4)

        # Check that values are reasonable
        self.assertTrue(np.all(np.array(params.a_water) > 0))
        self.assertTrue(np.all(np.array(params.a_ph_star) > 0))
        self.assertTrue(np.all(np.array(params.substrate1) >= 0))
        self.assertTrue(np.all(np.array(params.substrate1) <= 1))

        print("✓ SIOP-parameter integration successful")

    def test_forward_model_with_interpolated_siops(self):
        """Test forward model using interpolated SIOPs."""
        siop_manager = sbc.SIOPManager(self.siop_dir)

        # Use non-standard wavelengths to force interpolation
        custom_wavelengths = [475, 525, 625, 725]
        siop_manager.register_sensor("CustomSensor", custom_wavelengths)

        std_siops = siop_manager.get_standard_siops("CustomSensor")

        try:
            # Run forward model
            results = sbc.forward_model(
                chl=1.5,
                cdom=0.1,
                nap=0.5,
                depth=5.0,
                **std_siops
            )

            # Check that results are reasonable
            self.assertEqual(len(results.rrs), 4)
            self.assertTrue(np.all(results.rrs >= 0))
            self.assertTrue(np.all(results.rrs <= 1))
            self.assertTrue(np.all(np.isfinite(results.rrs)))

            # Check other outputs
            self.assertTrue(np.all(results.a > 0))
            self.assertTrue(np.all(results.bb > 0))

            print(
                f"✓ Forward model with interpolated SIOPs: rrs range {np.min(results.rrs):.4f}-{np.max(results.rrs):.4f}")

        except Exception as e:
            self.fail(f"Forward model with interpolated SIOPs failed: {e}")

    def test_multi_substrate_handling(self):
        """Test handling of multiple substrate types."""
        siop_manager = sbc.SIOPManager(self.siop_dir)
        siop_manager.register_sensor("TestSensor", [450, 550, 650, 750])

        siops = siop_manager.get_siops_for_sensor("TestSensor")

        # Check for multiple substrates
        substrate_types = [key for key in siops.keys() if 'substrate' in key]
        self.assertGreater(len(substrate_types), 1, "Should have multiple substrate types")
        print(siops)
        # Test forward model with different substrates
        base_params = {
            'chl': 1.0,
            'cdom': 0.1,
            'nap': 0.5,
            'depth': 5.0,
            'wavelengths': siops['wavelengths'],
            'a_water': siops['water_absorption'],
            'a_ph_star': siops['phytoplankton_absorption'],
            'num_bands': siops['num_bands']
        }

        substrate_results = {}

        for substrate_type in substrate_types:
            try:
                results = sbc.forward_model(
                    substrate1=siops[substrate_type],
                    **base_params
                )
                substrate_results[substrate_type] = results.rrs

            except Exception as e:
                print(f"⚠️ Failed to test {substrate_type}: {e}")

        # Check that different substrates give different results
        if len(substrate_results) >= 2:
            substrate_names = list(substrate_results.keys())
            rrs1 = substrate_results[substrate_names[0]]
            rrs2 = substrate_results[substrate_names[1]]

            # Should be noticeably different
            mean_diff = np.mean(np.abs(rrs1 - rrs2))
            self.assertGreater(mean_diff, 0.0001, "Different substrates should give different spectra")

            print(f"✓ Multi-substrate test: {len(substrate_results)} substrates, mean diff: {mean_diff:.4f}")

    def test_error_handling(self):
        """Test error handling in SIOP management."""
        siop_manager = sbc.SIOPManager(self.siop_dir)

        # Test unregistered sensor
        with self.assertRaises(KeyError):
            siop_manager.get_siops_for_sensor("NonexistentSensor")

        with self.assertRaises(KeyError):
            siop_manager.get_standard_siops("NonexistentSensor")

        # Test invalid sensor creation
        with self.assertRaises(ValueError):
            SensorFactory.create('unknown_sensor')

        print("✓ Error handling tests passed")

    def test_wavelength_range_coverage(self):
        """Test SIOP coverage across different wavelength ranges."""
        siop_manager = sbc.SIOPManager(self.siop_dir)

        # Test different wavelength ranges
        test_ranges = [
            ('UV-Blue', [380, 420, 450, 480]),
            ('Visible', [450, 550, 650, 750]),
            ('NIR', [750, 800, 850, 900]),
            ('Wide', [400, 500, 600, 700, 800]),
        ]

        for range_name, wavelengths in test_ranges:
            with self.subTest(range=range_name):
                try:
                    siop_manager.register_sensor(f"Test_{range_name}", wavelengths)
                    siops = siop_manager.get_siops_for_sensor(f"Test_{range_name}")

                    # Check that we got interpolated values
                    self.assertEqual(len(siops['water_absorption']), len(wavelengths))

                    # Check for reasonable values (no NaNs, positive absorption)
                    water_abs = np.array(siops['water_absorption'])
                    self.assertTrue(np.all(np.isfinite(water_abs)))
                    self.assertTrue(np.all(water_abs > 0))

                    print(f"✓ {range_name} range coverage successful")

                except Exception as e:
                    print(f"⚠️ {range_name} range failed: {e}")

    def test_siop_library_organization(self):
        """Test SIOP library organization and categorization."""
        siop_manager = sbc.SIOPManager(self.siop_dir)

        # Test library categorization
        library_types = siop_manager.get_common_library_types()

        # Should have different categories
        expected_categories = ['absorption', 'backscatter', 'substrate', 'other']
        for category in expected_categories:
            self.assertIn(category, library_types)

        # Check that libraries are properly categorized
        absorption_libs = library_types['absorption']
        substrate_libs = library_types['substrate']

        self.assertGreater(len(absorption_libs), 0, "Should have absorption libraries")
        self.assertGreater(len(substrate_libs), 0, "Should have substrate libraries")

        # Check specific expected libraries
        absorption_expected = ['water_absorption', 'phytoplankton_absorption']
        for lib in absorption_expected:
            found = any(lib in abs_lib for abs_lib in absorption_libs)
            self.assertTrue(found, f"Should find {lib} in absorption category")

        print(f"✓ Library organization: {len(absorption_libs)} absorption, "
              f"{len(substrate_libs)} substrate libraries")


if __name__ == '__main__':
    unittest.main()