"""Updated unit tests for sambuca_core package."""

import os
import shutil
import tempfile

import numpy as np
import pytest

import sambuca.core as sbc


class TestForwardModel:
    """Test the forward model functionality."""

    def setup_method(self):
        """Set up test data for each test."""
        self.num_bands = 4
        self.wavelengths = np.array([450, 550, 650, 750])
        self.a_water = np.array([0.01, 0.02, 0.1, 0.5])
        self.a_ph_star = np.array([0.05, 0.03, 0.02, 0.01])
        self.substrate1 = np.array([0.1, 0.2, 0.3, 0.4])
        self.substrate2 = np.array([0.05, 0.15, 0.25, 0.35])

    def test_forward_model_basic(self):
        """Test the forward model with basic inputs."""
        results = sbc.forward_model(
            chl=1.5,
            cdom=0.5,
            nap=2.0,
            depth=5.0,
            substrate1=self.substrate1,
            wavelengths=self.wavelengths,
            a_water=self.a_water,
            a_ph_star=self.a_ph_star,
            num_bands=self.num_bands
        )

        # Check that results object has expected attributes
        assert hasattr(results, 'rrs')
        assert hasattr(results, 'rrsdp')
        assert hasattr(results, 'r_0_minus')
        assert hasattr(results, 'a')
        assert hasattr(results, 'bb')
        assert hasattr(results, 'kd')

        # Check array shapes
        assert len(results.rrs) == self.num_bands
        assert len(results.rrsdp) == self.num_bands
        assert len(results.a) == self.num_bands
        assert len(results.bb) == self.num_bands

        # Check that reflectance values are reasonable
        assert np.all(results.rrs >= 0)
        assert np.all(results.rrs <= 1)
        assert np.all(results.a > 0)
        assert np.all(results.bb > 0)

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

        # Check substrate reflectance
        np.testing.assert_array_almost_equal(results1.r_substratum, self.substrate1)
        np.testing.assert_array_almost_equal(results2.r_substratum, self.substrate2)

    def test_forward_model_input_validation(self):
        """Test input validation."""
        # Test mismatched array lengths
        with pytest.raises(AssertionError):
            sbc.forward_model(
                chl=1.0, cdom=0.1, nap=0.5, depth=5.0,
                substrate1=self.substrate1[:-1],  # Wrong length
                wavelengths=self.wavelengths,
                a_water=self.a_water,
                a_ph_star=self.a_ph_star,
                num_bands=self.num_bands
            )


# Pytest configuration and fixtures
@pytest.fixture
def temp_siop_dir():
    """Create temporary SIOP directory for testing."""
    temp_dir = tempfile.mkdtemp()

    # Create minimal test SIOPs
    import pandas as pd
    wavelengths = np.array([450, 550, 650, 750])

    # Water absorption
    water_abs = np.array([0.01, 0.02, 0.1, 0.5])
    df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': water_abs})
    df.to_csv(os.path.join(temp_dir, 'water_absorption.csv'), index=False)

    # Phytoplankton absorption
    ph_abs = np.array([0.05, 0.03, 0.02, 0.01])
    df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': ph_abs})
    df.to_csv(os.path.join(temp_dir, 'phytoplankton_absorption.csv'), index=False)

    # Sand substrate
    sand_refl = np.array([0.1, 0.2, 0.3, 0.4])
    df = pd.DataFrame({'Wavelength': wavelengths, 'Reflectance': sand_refl})
    df.to_csv(os.path.join(temp_dir, 'sand_substrate.csv'), index=False)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)
