import os
import shutil
import tempfile
import unittest

import numpy as np
import pandas as pd

import sambuca.core as sbc
from sambuca.core.inversion import InversionParameters, LookUpTable


class TestLookUpTableIntegration(unittest.TestCase):
    """Integration tests for LUT functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.create_test_siops()
        self.setup_parameters()

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def create_test_siops(self):
        """Create test SIOP files."""
        self.siop_dir = os.path.join(self.temp_dir, 'siops')
        os.makedirs(self.siop_dir)

        wavelengths = np.array([450, 550, 650])

        water_abs = np.array([0.01, 0.02, 0.1])
        df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': water_abs})
        df.to_csv(os.path.join(self.siop_dir, 'water_absorption.csv'), index=False)

        ph_abs = np.array([0.05, 0.03, 0.02])
        df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': ph_abs})
        df.to_csv(os.path.join(self.siop_dir, 'phytoplankton_absorption.csv'), index=False)

        sand_refl = np.array([0.1, 0.2, 0.3])
        df = pd.DataFrame({'Wavelength': wavelengths, 'Reflectance': sand_refl})
        df.to_csv(os.path.join(self.siop_dir, 'sand_substrate.csv'), index=False)

    def setup_parameters(self):
        """Set up inversion parameters."""
        siop_manager = sbc.SIOPManager(self.siop_dir)
        siop_manager.register_sensor("TestSensor", [450, 550, 650])

        self.params = InversionParameters(
            chl=(0.5, 3.0),
            depth=(1.0, 10.0),
            fixed_cdom=0.1,
            fixed_nap=0.5,
            wavelengths=[450, 550, 650]
        )
        self.params.update_from_siop_manager(siop_manager, "TestSensor")

    def test_lut_creation_and_usage(self):
        """Test LUT creation and basic usage."""
        lut = LookUpTable(self.params)

        # Build small LUT
        lut.build_table(grid_size=5, progress_bar=False)

        self.assertTrue(lut.table_built)
        self.assertEqual(len(lut.param_array), 25)  # 5x5 grid

        # Test LUT inversion
        # Generate synthetic observation
        results = sbc.forward_model(
            chl=2.0,
            cdom=0.1,
            nap=0.5,
            depth=5.0,
            wavelengths=self.params.wavelengths,
            a_water=self.params.a_water,
            a_ph_star=self.params.a_ph_star,
            substrate1=self.params.substrate1,
            num_bands=3
        )

        # Invert using LUT
        lut_result = lut.invert(results.rrs, refine=False)

        self.assertIn('parameters', lut_result)
        self.assertIn('error', lut_result)

    def test_lut_save_and_load(self):
        """Test LUT save and load functionality."""
        lut1 = LookUpTable(self.params)
        lut1.build_table(grid_size=3, progress_bar=False)

        # Save LUT using non-compressed format for simpler testing
        lut_file = os.path.join(self.temp_dir, 'test_lut.pkl')
        lut1.save(lut_file, compressed=False)
        self.assertTrue(os.path.exists(lut_file))

        # Load LUT
        lut2 = LookUpTable.load(lut_file, build_kdtree=False)

        self.assertTrue(lut2.table_built)
        np.testing.assert_array_equal(lut1.param_array, lut2.param_array)
        np.testing.assert_array_equal(lut1.spectra_array, lut2.spectra_array)

    def test_lut_save_and_load_compressed(self):
        """Test LUT save and load functionality with compressed format."""
        lut1 = LookUpTable(self.params)
        lut1.build_table(grid_size=3, progress_bar=False)

        # Save LUT using compressed format (default)
        lut_file = os.path.join(self.temp_dir, 'test_lut_compressed')
        lut1.save(lut_file, compressed=True)

        # Check that compressed files exist
        self.assertTrue(os.path.exists(lut_file + "_arrays.npz"))
        self.assertTrue(os.path.exists(lut_file + "_param_values.npz"))
        self.assertTrue(os.path.exists(lut_file + "_attrs"))

        # Load LUT
        lut2 = LookUpTable.load(lut_file, build_kdtree=False)

        self.assertTrue(lut2.table_built)
        np.testing.assert_array_equal(lut1.param_array, lut2.param_array)
        np.testing.assert_array_equal(lut1.spectra_array, lut2.spectra_array)
