"""Updated integration tests for sambuca.cor package."""

import os
import shutil
import tempfile
import unittest

import numpy as np

from sambuca.core.results import ImageInversionResult


class TestResultsIntegration(unittest.TestCase):
    """Integration tests for results handling and visualization."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.create_mock_results()

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def create_mock_results(self):
        """Create mock inversion results for testing."""
        # Create synthetic result data
        height, width = 50, 50

        self.results = {
            'depth': np.random.uniform(1, 10, (height, width)),
            'chl': np.random.uniform(0.5, 3.0, (height, width)),
            'error': np.random.uniform(0.001, 0.01, (height, width)),
            'convergence': np.random.choice([True, False], (height, width), p=[0.8, 0.2])
        }

        # Add some NaN values to simulate invalid pixels
        invalid_mask = np.random.choice([True, False], (height, width), p=[0.1, 0.9])
        for param in ['depth', 'chl', 'error']:
            self.results[param][invalid_mask] = np.nan

        # Mock metadata
        self.metadata = {
            'driver': 'GTiff',
            'dtype': 'uint16',
            'width': width,
            'height': height,
            'count': 4,
            'crs': 'EPSG:4326'
        }

        self.workflow_config = {
            'workflow_type': 'BathymetryWorkflow',
            'sensor': 'sentinel2'
        }

    def test_image_result_creation(self):
        """Test ImageInversionResult creation and basic functionality."""
        result = ImageInversionResult(
            results=self.results,
            image_metadata=self.metadata,
            workflow_config=self.workflow_config,
            image_path="test_image.tif"
        )

        # Test basic properties
        param_names = result.get_parameter_names()
        self.assertIn('depth', param_names)
        self.assertIn('chl', param_names)
        self.assertNotIn('error', param_names)  # Error is not a parameter

        # Test parameter map access
        depth_map = result.get_parameter_map('depth')
        self.assertEqual(depth_map.shape, (50, 50))

    def test_result_statistics(self):
        """Test statistics calculation."""
        result = ImageInversionResult(
            results=self.results,
            image_metadata=self.metadata,
            workflow_config=self.workflow_config,
            image_path="test_image.tif"
        )

        stats = result.get_statistics()

        # Check that statistics were calculated for each parameter
        self.assertIn('depth', stats)
        self.assertIn('chl', stats)

        # Check statistics structure
        depth_stats = stats['depth']
        self.assertIn('valid_pixels', depth_stats)
        self.assertIn('mean', depth_stats)
        self.assertIn('std', depth_stats)
        self.assertIn('min', depth_stats)
        self.assertIn('max', depth_stats)

    def test_result_saving(self):
        """Test result saving functionality."""
        result = ImageInversionResult(
            results=self.results,
            image_metadata=self.metadata,
            workflow_config=self.workflow_config,
            image_path="test_image.tif"
        )

        # Test saving all parameters
        output_dir = os.path.join(self.temp_dir, 'output')
        saved_files = result.save_all_parameters(
            output_dir,
            formats=['tiff'],
            prefix='test'
        )

        # Check that files were created
        self.assertTrue(os.path.exists(output_dir))
        self.assertIn('depth_tiff', saved_files)
        self.assertIn('chl_tiff', saved_files)

        # Check that TIFF files exist
        self.assertTrue(os.path.exists(saved_files['depth_tiff']))
        self.assertTrue(os.path.exists(saved_files['chl_tiff']))
