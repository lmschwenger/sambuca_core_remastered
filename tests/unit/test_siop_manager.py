import os
import shutil
import tempfile

import numpy as np
import pytest

import sambuca.core as sbc


class TestSIOPManager:
    """Test the SIOP Manager functionality."""

    def setup_method(self):
        """Set up test SIOP directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.create_test_siops()
        self.siop_manager = sbc.SIOPManager(self.temp_dir)

    def teardown_method(self):
        """Clean up test directory."""
        shutil.rmtree(self.temp_dir)

    def create_test_siops(self):
        """Create test SIOP files."""
        import pandas as pd

        wavelengths = np.arange(400, 801, 10)

        # Water absorption
        water_abs = 0.01 + 0.001 * (wavelengths - 400) / 10
        df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': water_abs})
        df.to_csv(os.path.join(self.temp_dir, 'water_absorption.csv'), index=False)

        # Phytoplankton absorption
        ph_abs = 0.02 * np.exp(-0.01 * (wavelengths - 440) ** 2) + 0.01
        df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': ph_abs})
        df.to_csv(os.path.join(self.temp_dir, 'phytoplankton_absorption.csv'), index=False)

        # Sand substrate
        sand_refl = 0.1 + 0.3 * (wavelengths - 400) / 400
        df = pd.DataFrame({'Wavelength': wavelengths, 'Reflectance': sand_refl})
        df.to_csv(os.path.join(self.temp_dir, 'sand_substrate.csv'), index=False)

    def test_siop_loading(self):
        """Test SIOP loading functionality."""
        libraries = self.siop_manager.list_available_libraries()

        expected_libs = ['water_absorption', 'phytoplankton_absorption', 'sand_substrate']
        for lib in expected_libs:
            assert lib in libraries

    def test_sensor_registration(self):
        """Test sensor registration and wavelength interpolation."""
        test_wavelengths = [450, 550, 650, 750]
        self.siop_manager.register_sensor("TestSensor", test_wavelengths)

        siops = self.siop_manager.get_siops_for_sensor("TestSensor")

        # Check wavelengths match
        np.testing.assert_array_equal(siops['wavelengths'], test_wavelengths)

        # Check expected SIOPs are present
        expected_siops = ['water_absorption', 'phytoplankton_absorption', 'sand_substrate']
        for siop in expected_siops:
            assert siop in siops
            assert len(siops[siop]) == len(test_wavelengths)

    def test_standard_siops(self):
        """Test standard SIOP retrieval."""
        self.siop_manager.register_sensor("TestSensor", [450, 550, 650])

        std_siops = self.siop_manager.get_standard_siops("TestSensor")

        # Check required components
        required_components = ['wavelengths', 'num_bands', 'a_water', 'a_ph_star', 'substrate1']
        for component in required_components:
            assert component in std_siops

    def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(KeyError):
            self.siop_manager.get_siops_for_sensor("NonexistentSensor")
