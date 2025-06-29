"""Unit tests for sambuca.core.results modules."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from sambuca.core.results.image_result import ImageInversionResult


class TestImageInversionResult:
    """Test ImageInversionResult functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create sample results
        height, width = 50, 50
        self.results = {
            'depth': np.random.uniform(0.5, 20.0, (height, width)),
            'chl': np.random.uniform(0.1, 10.0, (height, width)),
            'cdom': np.random.uniform(0.001, 0.1, (height, width)),
            'nap': np.random.uniform(0.001, 5.0, (height, width)),
            'error': np.random.uniform(0.001, 0.1, (height, width)),
            'convergence': np.random.choice([True, False], (height, width))
        }

        # Add some NaN values to simulate invalid pixels
        self.results['depth'][10:15, 10:15] = np.nan
        self.results['chl'][5:8, 5:8] = np.nan

        # Mock metadata
        self.image_metadata = {
            'width': width,
            'height': height,
            'count': 4,
            'crs': 'EPSG:4326',
            'transform': [1.0, 0.0, 0.0, 0.0, -1.0, 50.0],
            'dtype': 'float32'
        }

        self.workflow_config = {
            'sensor': 'sentinel2',
            'method': 'optimization',
            'wavelengths': [443, 490, 560, 665]
        }

        self.image_path = "test_image.tif"

        # Create result object
        self.result = ImageInversionResult(
            self.results,
            self.image_metadata,
            self.workflow_config,
            self.image_path
        )

    def test_initialization(self):
        """Test proper initialization of ImageInversionResult."""
        assert self.result.results == self.results
        assert self.result.image_metadata == self.image_metadata
        assert self.result.workflow_config == self.workflow_config
        assert self.result.image_path == self.image_path
        assert self.result._stats_cache is None

    def test_get_parameter_names(self):
        """Test getting parameter names."""
        param_names = self.result.get_parameter_names()

        expected_params = ['depth', 'chl', 'cdom', 'nap']
        assert set(param_names) == set(expected_params)

        # Should not include metadata fields
        assert 'error' not in param_names
        assert 'convergence' not in param_names

    def test_get_parameter_map_valid(self):
        """Test getting valid parameter map."""
        depth_map = self.result.get_parameter_map('depth')

        assert isinstance(depth_map, np.ndarray)
        assert depth_map.shape == (50, 50)
        assert np.array_equal(depth_map[~np.isnan(depth_map)], self.results['depth'][~np.isnan(self.results['depth'])])

    def test_get_parameter_map_invalid(self):
        """Test getting invalid parameter map."""
        with pytest.raises(ValueError, match="Parameter 'invalid' not found"):
            self.result.get_parameter_map('invalid')

    def test_get_statistics_comprehensive(self):
        """Test comprehensive statistics calculation."""
        stats = self.result.get_statistics()

        # Should have stats for all parameters
        expected_params = ['depth', 'chl', 'cdom', 'nap']
        for param in expected_params:
            assert param in stats

            param_stats = stats[param]
            assert 'valid_pixels' in param_stats
            assert 'total_pixels' in param_stats
            assert 'valid_percentage' in param_stats
            assert 'min' in param_stats
            assert 'max' in param_stats
            assert 'mean' in param_stats
            assert 'median' in param_stats
            assert 'std' in param_stats
            assert 'p25' in param_stats
            assert 'p75' in param_stats

            # Check that statistics make sense
            assert 0 <= param_stats['valid_percentage'] <= 100
            assert param_stats['min'] <= param_stats['max']
            assert param_stats['p25'] <= param_stats['median'] <= param_stats['p75']

    def test_get_statistics_with_nan_handling(self):
        """Test statistics calculation with NaN values."""
        stats = self.result.get_statistics()

        # Depth has NaN values in 10:15, 10:15 region (25 pixels)
        depth_stats = stats['depth']
        assert depth_stats['valid_pixels'] < depth_stats['total_pixels']
        assert depth_stats['valid_percentage'] < 100

        # CHL has NaN values in 5:8, 5:8 region (9 pixels)
        chl_stats = stats['chl']
        assert chl_stats['valid_pixels'] < chl_stats['total_pixels']

    def test_get_statistics_error_and_convergence(self):
        """Test statistics for error and convergence."""
        stats = self.result.get_statistics()

        # Should include error statistics
        assert 'error' in stats
        error_stats = stats['error']
        assert 'min' in error_stats
        assert 'max' in error_stats
        assert 'mean' in error_stats
        assert 'median' in error_stats

        # Should include convergence statistics
        assert 'convergence' in stats
        conv_stats = stats['convergence']
        assert 'converged_pixels' in conv_stats
        assert 'total_pixels' in conv_stats
        assert 'convergence_rate' in conv_stats
        assert 0 <= conv_stats['convergence_rate'] <= 100

    def test_get_statistics_caching(self):
        """Test statistics caching functionality."""
        # First call should calculate
        stats1 = self.result.get_statistics()
        assert self.result._stats_cache is not None

        # Second call should use cache
        stats2 = self.result.get_statistics()
        assert stats1 is stats2  # Should be same object

        # Force recalculation
        stats3 = self.result.get_statistics(force_recalculate=True)
        assert stats1 is not stats3  # Should be different object
        assert stats1 == stats3  # But same values

    def test_print_summary(self, capsys):
        """Test summary printing functionality."""
        self.result.print_summary()

        captured = capsys.readouterr()
        output = captured.out

        # Check that summary contains expected elements
        assert "INVERSION RESULTS SUMMARY" in output
        assert "DEPTH:" in output
        assert "CHL:" in output
        assert "Valid pixels:" in output
        assert "ERROR STATISTICS:" in output
        assert "CONVERGENCE:" in output

    def test_extract_transect_invalid_parameter(self):
        """Test transect extraction with invalid parameter."""
        with pytest.raises(KeyError):
            self.result.extract_transect((0, 0), (10, 10), 'invalid_param')


class TestImageInversionResultFileIO:
    """Test file I/O functionality of ImageInversionResult."""

    def setup_method(self):
        """Set up test fixtures with file I/O focus."""
        self.temp_dir = tempfile.mkdtemp()

        # Create minimal test results
        height, width = 20, 20
        self.results = {
            'depth': np.random.uniform(1.0, 15.0, (height, width)),
            'chl': np.random.uniform(0.5, 5.0, (height, width)),
            'error': np.random.uniform(0.01, 0.05, (height, width))
        }

        self.image_metadata = {
            'width': width,
            'height': height,
            'count': 1,
            'crs': 'EPSG:4326',
            'transform': [1.0, 0.0, 0.0, 0.0, -1.0, 20.0],
            'dtype': 'float32'
        }

        self.result = ImageInversionResult(
            self.results,
            self.image_metadata,
            {},
            "test.tif"
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch('rasterio.open')
    def test_save_depth_map_tiff(self, mock_rasterio_open):
        """Test saving depth map as GeoTIFF."""
        mock_dataset = Mock()
        mock_rasterio_open.return_value.__enter__.return_value = mock_dataset

        output_path = Path(self.temp_dir) / "depth.tif"

        self.result.save_depth_map(str(output_path), fmt='tiff')

        # Verify rasterio.open was called with correct parameters
        mock_rasterio_open.assert_called_once()
        call_args = mock_rasterio_open.call_args

        # Verify dataset.write was called
        mock_dataset.write.assert_called_once()
        mock_dataset.set_band_description.assert_called_once_with(1, 'depth')

    @patch('matplotlib.pyplot.close')
    @patch('matplotlib.pyplot.colorbar')
    @patch('matplotlib.pyplot.subplots')
    def test_save_depth_map_png(self, mock_subplots, mock_colorbar, mock_plt_close):
        """Test saving depth map as PNG."""
        # Mock matplotlib components
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)
        mock_im = Mock()
        mock_ax.imshow.return_value = mock_im

        output_path = Path(self.temp_dir) / "depth.png"

        self.result.save_depth_map(str(output_path), fmt='png')

        # Verify matplotlib calls
        mock_subplots.assert_called_once_with(figsize=(10, 8))
        mock_ax.imshow.assert_called_once()
        mock_ax.set_title.assert_called_once()
        mock_colorbar.assert_called_once()
        mock_fig.savefig.assert_called_once_with(output_path, dpi=300, bbox_inches='tight')
        mock_plt_close.assert_called_once_with(mock_fig)

    def test_save_depth_map_no_depth_data(self):
        """Test saving depth map when no depth data available."""
        # Remove depth from results
        del self.result.results['depth']

        output_path = Path(self.temp_dir) / "depth.tif"

        with pytest.raises(ValueError, match="No depth data available"):
            self.result.save_depth_map(str(output_path))

    def test_save_depth_map_invalid_format(self):
        """Test saving depth map with invalid format."""
        output_path = Path(self.temp_dir) / "depth.xyz"

        with pytest.raises(ValueError, match="Unsupported format"):
            self.result.save_depth_map(str(output_path), fmt='xyz')

    @patch('rasterio.open')
    @patch('matplotlib.pyplot.close')
    @patch('matplotlib.pyplot.colorbar')
    @patch('matplotlib.pyplot.subplots')
    def test_save_all_parameters(self, mock_subplots, mock_colorbar, mock_plt_close, mock_rasterio_open):
        """Test saving all parameters."""
        # Mock rasterio
        mock_dataset = Mock()
        mock_rasterio_open.return_value.__enter__.return_value = mock_dataset

        # Mock matplotlib for PNG saving
        mock_fig = Mock()
        mock_ax = Mock()
        mock_subplots.return_value = (mock_fig, mock_ax)
        mock_im = Mock()
        mock_ax.imshow.return_value = mock_im

        output_dir = Path(self.temp_dir) / "output"

        saved_files = self.result.save_all_parameters(
            str(output_dir),
            formats=['tiff', 'png'],
            prefix='test'
        )

        # Should have saved both parameters in both formats
        expected_files = [
            'depth_tiff', 'depth_png',
            'chl_tiff', 'chl_png'
        ]

        assert len(saved_files) == len(expected_files)
        for key in expected_files:
            assert key in saved_files
            assert str(output_dir) in saved_files[key]

        # Verify directory was created
        assert output_dir.exists()


class TestResultsIntegration:
    """Integration tests for results modules."""

    def setup_method(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up integration test environment."""
        shutil.rmtree(self.temp_dir)

    def test_end_to_end_result_workflow(self):
        """Test complete workflow from results to visualization and saving."""
        # Create realistic test results
        height, width = 40, 40

        # Simulate realistic depth values
        x, y = np.meshgrid(np.linspace(0, 1, width), np.linspace(0, 1, height))
        depth_base = 5 + 10 * (x + y) / 2  # Gradient from 5 to 15m
        depth_noise = np.random.normal(0, 0.5, (height, width))
        depth = depth_base + depth_noise

        # Simulate chl with some correlation to depth
        chl = 2.0 + 3.0 * np.exp(-depth / 10) + np.random.normal(0, 0.2, (height, width))

        # Simulate error inversely related to depth (shallower = higher error)
        error = 0.01 + 0.05 * np.exp(-depth / 5) + np.random.uniform(0, 0.01, (height, width))

        # Add some invalid pixels
        mask = np.random.choice([True, False], (height, width), p=[0.8, 0.2])
        depth[~mask] = np.nan
        chl[~mask] = np.nan
        error[~mask] = np.nan

        results = {
            'depth': depth,
            'chl': chl,
            'error': error,
            'convergence': mask
        }

        # Create realistic metadata
        metadata = {
            'width': width,
            'height': height,
            'count': 1,
            'crs': 'EPSG:32633',
            'transform': [10.0, 0.0, 500000.0, 0.0, -10.0, 6000000.0],
            'dtype': 'float32'
        }

        config = {
            'sensor': 'sentinel2',
            'method': 'optimization',
            'wavelengths': [443, 490, 560, 665]
        }

        # Create result object
        result = ImageInversionResult(results, metadata, config, "test_image.tif")

        # Test statistics calculation
        stats = result.get_statistics()

        assert 'depth' in stats
        assert 'chl' in stats
        assert 'error' in stats
        assert 'convergence' in stats

        # Verify realistic statistics
        depth_stats = stats['depth']
        assert 4 < depth_stats['mean'] < 16  # Should be in expected range
        assert depth_stats['valid_percentage'] < 100  # Some invalid pixels

    def test_statistics_validation(self):
        """Test that statistics are mathematically consistent."""
        # Create test data with known statistics
        height, width = 100, 100

        # Create uniform data for validation
        depth = np.full((height, width), 10.0)
        depth[50:, :] = 20.0  # Half the image is different depth

        # Add some invalid pixels
        depth[0:10, 0:10] = np.nan  # 100 invalid pixels

        results = {
            'depth': depth,
            'error': np.full((height, width), 0.05)
        }

        result = ImageInversionResult(results, {}, {}, "test.tif")
        stats = result.get_statistics()

        depth_stats = stats['depth']

        # Validate pixel counts
        assert depth_stats['total_pixels'] == 10000
        assert depth_stats['valid_pixels'] == 9900  # 10000 - 100 invalid
        assert abs(depth_stats['valid_percentage'] - 99.0) < 0.1

        # Validate statistics for bimodal distribution
        assert depth_stats['min'] == 10.0
        assert depth_stats['max'] == 20.0
        assert abs(depth_stats['mean'] - 15.0) < 0.1  # Should be close to 15
        assert abs(depth_stats['median'] - 20.0) < 0.1

    def test_error_handling_edge_cases(self):
        """Test error handling for edge cases."""
        # Test with all-NaN data
        height, width = 10, 10
        results = {
            'depth': np.full((height, width), np.nan),
            'chl': np.random.uniform(0.1, 10, (height, width))
        }

        result = ImageInversionResult(results, {}, {}, "test.tif")
        stats = result.get_statistics()

        # Depth should have zero valid pixels
        assert stats['depth']['valid_pixels'] == 0
        assert stats['depth']['valid_percentage'] == 0.0
        assert 'min' not in stats['depth']  # No min/max for all-NaN

        # CHL should have normal statistics
        assert stats['chl']['valid_pixels'] > 0
        assert 'min' in stats['chl']
