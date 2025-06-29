import os
import shutil
import tempfile

import numpy as np

from sambuca.core.workflows import BathymetryWorkflow


class TestWorkflows:
    """Test workflow functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.create_test_siops()

    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir)

    def create_test_siops(self):
        """Create minimal test SIOP files."""
        import pandas as pd

        wavelengths = np.array([492.4, 559.8, 664.6, 704.1])  # Sentinel-2 bands

        # Create minimal required SIOPs
        water_abs = np.array([0.0105, 0.0162, 0.3946, 0.6250])
        df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': water_abs})
        df.to_csv(os.path.join(self.temp_dir, 'water_absorption.csv'), index=False)

        ph_abs = np.array([0.0280, 0.0200, 0.0120, 0.0100])
        df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': ph_abs})
        df.to_csv(os.path.join(self.temp_dir, 'phytoplankton_absorption.csv'), index=False)

        sand_refl = np.array([0.15, 0.25, 0.35, 0.40])
        df = pd.DataFrame({'Wavelength': wavelengths, 'Reflectance': sand_refl})
        df.to_csv(os.path.join(self.temp_dir, 'sand_substrate.csv'), index=False)

    def test_bathymetry_workflow_creation(self):
        """Test bathymetry workflow creation."""
        workflow = BathymetryWorkflow(self.temp_dir, sensor='sentinel2')

        assert workflow.sensor_name == 'sentinel2'
        assert hasattr(workflow, 'inversion_params')
        assert hasattr(workflow, 'siop_manager')

    def test_bathymetry_workflow_customization(self):
        """Test parameter customization in workflow."""
        workflow = BathymetryWorkflow(self.temp_dir, sensor='sentinel2')

        # Test parameter customization
        workflow.customize_parameters(
            depth=(0, 20),
            fixed_chl=1.5
        )

        assert workflow.inversion_params.depth == (0, 20)
        assert workflow.inversion_params.fixed_chl == 1.5

    def test_workflow_config(self):
        """Test workflow configuration retrieval."""
        workflow = BathymetryWorkflow(self.temp_dir, sensor='sentinel2')

        config = workflow.get_config()

        assert 'workflow_type' in config
        assert 'sensor' in config
        assert config['workflow_type'] == 'BathymetryWorkflow'
        assert config['sensor'] == 'sentinel2'
