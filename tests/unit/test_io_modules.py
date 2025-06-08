"""Unit tests for sambuca.core.io modules."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from sambuca.core.io.base import ImageData, BaseImageLoader
from sambuca.core.io.preprocessing import ImagePreprocessor
from sambuca.core.io.raster_loader import RasterImageLoader


class TestImageData:
    """Test ImageData container class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_data_bands_last = np.random.rand(100, 100, 4).astype(np.float32)
        self.test_data_bands_first = np.random.rand(4, 100, 100).astype(np.float32)
        self.metadata = {
            'width': 100,
            'height': 100,
            'count': 4,
            'dtype': 'float32'
        }

    def test_image_data_creation_bands_last(self):
        """Test ImageData creation with bands-last format."""
        image_data = ImageData(
            data=self.test_data_bands_last,
            metadata=self.metadata,
            filepath="test.tif"
        )

        assert image_data.shape == (100, 100, 4)
        assert image_data.is_bands_last is True
        assert image_data.filepath == "test.tif"

    def test_image_data_creation_bands_first(self):
        """Test ImageData creation with bands-first format."""
        image_data = ImageData(
            data=self.test_data_bands_first,
            metadata=self.metadata,
            filepath="test.tif"
        )

        assert image_data.shape == (4, 100, 100)
        assert image_data.is_bands_last is False

    def test_image_data_with_bands_info(self):
        """Test ImageData with band and wavelength information."""
        bands = [2, 3, 4, 8]
        wavelengths = [490.0, 560.0, 665.0, 842.0]

        image_data = ImageData(
            data=self.test_data_bands_last,
            metadata=self.metadata,
            filepath="test.tif",
            bands=bands,
            wavelengths=wavelengths
        )

        assert image_data.bands == bands
        assert image_data.wavelengths == wavelengths
        assert len(image_data.wavelengths) == image_data.shape[2]

    def test_is_bands_last_detection(self):
        """Test automatic detection of band ordering."""
        # Test with bands last (100, 100, 4) - 4 <= 100
        bands_last_data = np.random.rand(100, 100, 4).astype(np.float32)
        image_data_last = ImageData(bands_last_data, {}, "test.tif")
        assert image_data_last.is_bands_last is True

        # Test with bands first (4, 100, 100) - 100 > 4
        bands_first_data = np.random.rand(4, 100, 100).astype(np.float32)
        image_data_first = ImageData(bands_first_data, {}, "test.tif")
        assert image_data_first.is_bands_last is False


class TestBaseImageLoader:
    """Test abstract base image loader."""

    def test_base_loader_interface(self):
        """Test that BaseImageLoader is properly abstract."""
        with pytest.raises(TypeError):
            BaseImageLoader()

    def test_concrete_implementation(self):
        """Test concrete implementation of BaseImageLoader."""

        class TestLoader(BaseImageLoader):
            def load(self, filepath, bands=None):
                data = np.random.rand(100, 100, 4).astype(np.float32)
                metadata = {'width': 100, 'height': 100, 'count': 4}
                return ImageData(data, metadata, filepath, bands)

        loader = TestLoader()
        result = loader.load("test.tif", bands=[1, 2, 3, 4])

        assert isinstance(result, ImageData)
        assert result.filepath == "test.tif"
        assert result.bands == [1, 2, 3, 4]


class TestImagePreprocessor:
    """Test image preprocessing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

        # Create test image data
        self.test_data_bands_last = np.random.rand(50, 50, 4).astype(np.float32)
        self.test_data_bands_first = np.random.rand(4, 50, 50).astype(np.float32)

        # Add some NaN values for testing
        self.test_data_bands_last[10:15, 10:15, :] = np.nan
        self.test_data_bands_first[:, 10:15, 10:15] = np.nan

        self.metadata = {'width': 50, 'height': 50, 'count': 4}

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_apply_water_mask_no_mask_file(self):
        """Test water mask creation without mask file."""
        image_data = ImageData(
            data=self.test_data_bands_last,
            metadata=self.metadata,
            filepath="test.tif"
        )

        mask = ImagePreprocessor.apply_water_mask(image_data)

        assert mask.shape == (50, 50)
        assert mask.dtype == bool
        # Areas with NaN should be False
        assert not mask[12, 12]  # Should be False due to NaN
        assert mask[0, 0]  # Should be True for valid data

    def test_apply_water_mask_bands_first(self):
        """Test water mask with bands-first format."""
        image_data = ImageData(
            data=self.test_data_bands_first,
            metadata=self.metadata,
            filepath="test.tif"
        )

        mask = ImagePreprocessor.apply_water_mask(image_data)

        assert mask.shape == (50, 50)
        assert mask.dtype == bool
        # Areas with NaN should be False
        assert not mask[12, 12]  # Should be False due to NaN

    @patch('rasterio.open')
    def test_apply_water_mask_with_file(self, mock_rasterio):
        """Test water mask application with mask file."""
        # Mock rasterio dataset
        mock_dataset = Mock()
        mock_dataset.count = 1
        mock_dataset.read.return_value = np.random.rand(50, 50) > 0.5
        mock_rasterio.return_value.__enter__.return_value = mock_dataset

        image_data = ImageData(
            data=self.test_data_bands_last,
            metadata=self.metadata,
            filepath="test.tif"
        )

        mask = ImagePreprocessor.apply_water_mask(
            image_data,
            mask_path="water_mask.tif",
            mask_threshold=0.5
        )

        assert mask.shape == (50, 50)
        assert mask.dtype == bool
        mock_rasterio.assert_called_once_with("water_mask.tif")

    @patch('rasterio.open')
    def test_apply_water_mask_multiband_file(self, mock_rasterio):
        """Test water mask with multi-band mask file."""
        # Mock rasterio dataset with multiple bands
        mock_dataset = Mock()
        mock_dataset.count = 3
        mock_dataset.read.return_value = np.random.rand(50, 50) > 0.5
        mock_rasterio.return_value.__enter__.return_value = mock_dataset

        image_data = ImageData(
            data=self.test_data_bands_last,
            metadata=self.metadata,
            filepath="test.tif"
        )

        mask = ImagePreprocessor.apply_water_mask(image_data, mask_path="multi_mask.tif")

        # Should use the last band (count=3) when multiple bands available
        mock_dataset.read.assert_called_once_with(3)

    def test_extract_pixel_spectrum_bands_last(self):
        """Test pixel spectrum extraction for bands-last format."""
        image_data = ImageData(
            data=self.test_data_bands_last,
            metadata=self.metadata,
            filepath="test.tif"
        )

        spectrum = ImagePreprocessor.extract_pixel_spectrum(image_data, 5, 5)

        assert spectrum.shape == (4,)
        assert np.allclose(spectrum, self.test_data_bands_last[5, 5, :])

    def test_extract_pixel_spectrum_bands_first(self):
        """Test pixel spectrum extraction for bands-first format."""
        image_data = ImageData(
            data=self.test_data_bands_first,
            metadata=self.metadata,
            filepath="test.tif"
        )

        spectrum = ImagePreprocessor.extract_pixel_spectrum(image_data, 5, 5)

        assert spectrum.shape == (4,)
        assert np.allclose(spectrum, self.test_data_bands_first[:, 5, 5])

    def test_create_rgb_preview_bands_last(self):
        """Test RGB preview creation for bands-last format."""
        image_data = ImageData(
            data=self.test_data_bands_last,
            metadata=self.metadata,
            filepath="test.tif"
        )

        rgb = ImagePreprocessor.create_rgb_preview(
            image_data,
            rgb_bands=(2, 1, 0)
        )

        assert rgb.shape == (50, 50, 3)
        assert rgb.dtype == np.float32
        assert np.all(np.nanmin(rgb) >= 0) and np.all(np.nanmax(rgb) <= 1)

    def test_create_rgb_preview_bands_first(self):
        """Test RGB preview creation for bands-first format."""
        image_data = ImageData(
            data=self.test_data_bands_first,
            metadata=self.metadata,
            filepath="test.tif"
        )

        rgb = ImagePreprocessor.create_rgb_preview(
            image_data,
            rgb_bands=(3, 2, 1)
        )

        assert rgb.shape == (50, 50, 3)
        assert rgb.dtype == np.float32
        assert np.all(np.nanmin(rgb) >= 0) and np.all(np.nanmax(rgb) <= 1)

    def test_create_rgb_preview_with_stretching(self):
        """Test RGB preview with different stretch percentiles."""
        image_data = ImageData(
            data=self.test_data_bands_last,
            metadata=self.metadata,
            filepath="test.tif"
        )

        # Test with different stretch percentiles
        rgb_default = ImagePreprocessor.create_rgb_preview(
            image_data, stretch_percentiles=(2, 98)
        )
        rgb_aggressive = ImagePreprocessor.create_rgb_preview(
            image_data, stretch_percentiles=(5, 95)
        )

        # Both should be valid but likely different
        assert rgb_default.shape == rgb_aggressive.shape
        # Values might be different due to different stretching
        assert not np.array_equal(rgb_default, rgb_aggressive) or np.all(rgb_default == 0)

    def test_create_rgb_preview_invalid_bands(self):
        """Test RGB preview with invalid band indices."""
        image_data = ImageData(
            data=self.test_data_bands_last,
            metadata=self.metadata,
            filepath="test.tif"
        )

        # Use band indices that exceed available bands
        rgb = ImagePreprocessor.create_rgb_preview(
            image_data,
            rgb_bands=(10, 11, 12)  # These bands don't exist
        )

        # Should return zeros for invalid bands
        assert rgb.shape == (50, 50, 3)
        assert np.all(rgb == 0)


class TestRasterImageLoader:
    """Test raster image loader functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_loader_initialization(self):
        """Test loader initialization with different options."""
        loader = RasterImageLoader(
            auto_scale=True,
            convert_to_rrs=False,
            handle_nodata=True,
            bands_last=True
        )

        assert loader.auto_scale is True
        assert loader.convert_to_rrs is False
        assert loader.handle_nodata is True
        assert loader.bands_last is True

    def test_loader_initialization_defaults(self):
        """Test loader initialization with default values."""
        loader = RasterImageLoader()

        assert loader.auto_scale is True
        assert loader.convert_to_rrs is True
        assert loader.handle_nodata is True
        assert loader.bands_last is True

    @patch('rasterio.open')
    def test_load_image_success(self, mock_rasterio):
        """Test successful image loading."""
        # Mock rasterio dataset
        mock_dataset = Mock()
        mock_dataset.read.return_value = np.random.randint(
            0, 10000, (4, 100, 100), dtype=np.uint16
        )
        mock_dataset.meta = {
            'width': 100,
            'height': 100,
            'count': 4,
            'dtype': 'uint16'
        }
        mock_rasterio.return_value.__enter__.return_value = mock_dataset

        # Create a temporary file to mock file existence
        temp_file = Path(self.temp_dir) / "test.tif"
        temp_file.touch()

        loader = RasterImageLoader()
        result = loader.load(str(temp_file))

        assert isinstance(result, ImageData)
        assert result.shape == (100, 100, 4)  # bands_last=True by default
        assert str(temp_file) in result.filepath
        mock_rasterio.assert_called_once()

    @patch('rasterio.open')
    def test_load_specific_bands(self, mock_rasterio):
        """Test loading specific bands."""
        mock_dataset = Mock()
        mock_dataset.read.return_value = np.random.randint(
            0, 10000, (3, 100, 100), dtype=np.uint16
        )
        mock_dataset.meta = {
            'width': 100,
            'height': 100,
            'count': 8,  # Original has 8 bands
            'dtype': 'uint16'
        }
        mock_rasterio.return_value.__enter__.return_value = mock_dataset

        temp_file = Path(self.temp_dir) / "test.tif"
        temp_file.touch()

        loader = RasterImageLoader()
        result = loader.load(str(temp_file), bands=[2, 3, 4])

        assert result.shape == (100, 100, 3)
        assert result.bands == [2, 3, 4]
        mock_dataset.read.assert_called_once_with([2, 3, 4])

    def test_load_nonexistent_file(self):
        """Test loading non-existent file."""
        loader = RasterImageLoader()

        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent.tif")

    def test_handle_nodata_processing(self):
        """Test no-data value handling."""
        # Convert to float32 first, as _preprocess does
        data = np.array([[[100, 0, 65535, 5000]]], dtype=np.uint16).astype(np.float32)
        metadata = {'nodata': None, 'dtype': 'uint16'}

        processed = RasterImageLoader._handle_nodata(data, metadata)

        # Values <= 0 and >= 65,535 should become NaN
        assert np.isnan(processed[0, 0, 1])  # 0 value
        assert np.isnan(processed[0, 0, 2])  # 65535 value
        assert not np.isnan(processed[0, 0, 0])  # 100 value
        assert not np.isnan(processed[0, 0, 3])  # 5000 value

    def test_handle_nodata_with_metadata_value(self):
        """Test no-data handling with metadata value."""
        # Convert to float32 first, as _preprocess does
        data = np.array([[[100, 0, -9999, 5000]]], dtype=np.int16).astype(np.float32)
        metadata = {'nodata': -9999, 'dtype': 'int16'}

        processed = RasterImageLoader._handle_nodata(data, metadata)

        assert np.isnan(processed[0, 0, 2])  # -9999 value
        assert not np.isnan(processed[0, 0, 0])  # 100 value

    def test_apply_scaling_uint16(self):
        """Test automatic scaling for uint16 data."""
        data = np.array([[[5000, 8000, 2000]]], dtype=np.float32)
        metadata = {'dtype': 'uint16'}

        scaled = RasterImageLoader._apply_scaling(data, metadata)

        assert np.allclose(scaled, data / 10000.0)

    def test_apply_scaling_already_scaled(self):
        """Test scaling when data is already in reflectance units."""
        data = np.array([[[0.5, 0.8, 0.2]]], dtype=np.float32)
        metadata = {'dtype': 'float32'}

        scaled = RasterImageLoader._apply_scaling(data, metadata)

        # Should remain unchanged
        assert np.allclose(scaled, data)

    def test_apply_scaling_high_values(self):
        """Test scaling when data has high values (digital numbers)."""
        data = np.array([[[5000, 8000, 2000]]], dtype=np.float32)
        metadata = {'dtype': 'float32'}

        scaled = RasterImageLoader._apply_scaling(data, metadata)

        # Should be scaled by 10000 because max value > 10
        assert np.allclose(scaled, data / 10000.0)

    def test_convert_to_rrs(self):
        """Test conversion to remote sensing reflectance."""
        surface_reflectance = np.array([[[0.1, 0.2, 0.3]]], dtype=np.float32)

        rrs = RasterImageLoader._convert_to_rrs(surface_reflectance)

        # Currently this function just returns the input unchanged
        assert np.allclose(rrs, surface_reflectance)

    @patch('rasterio.open')
    def test_full_preprocessing_pipeline(self, mock_rasterio):
        """Test complete preprocessing pipeline."""
        # Create realistic test data
        raw_data = np.random.randint(1000, 5000, (4, 50, 50), dtype=np.uint16)
        raw_data[0, 10:15, 10:15] = 0  # Add some no-data
        raw_data[1, 5:8, 5:8] = 65535  # Add more no-data

        mock_dataset = Mock()
        mock_dataset.read.return_value = raw_data
        mock_dataset.meta = {
            'width': 50,
            'height': 50,
            'count': 4,
            'dtype': 'uint16',
            'nodata': None
        }
        mock_rasterio.return_value.__enter__.return_value = mock_dataset

        temp_file = Path(self.temp_dir) / "test.tif"
        temp_file.touch()

        loader = RasterImageLoader(
            auto_scale=True,
            convert_to_rrs=True,
            handle_nodata=True,
            bands_last=True
        )

        result = loader.load(str(temp_file))

        # Check final output
        assert result.shape == (50, 50, 4)
        assert result.data.dtype == np.float32

        # Check that no-data areas became NaN
        assert np.isnan(result.data[12, 12, 0])  # No-data area
        assert np.isnan(result.data[6, 6, 1])  # No-data area

        # Check that valid data is scaled properly
        valid_data = result.data[~np.isnan(result.data)]
        assert np.all(valid_data > 0)
        assert np.all(valid_data < 1)  # Should be in reflectance units

    def test_bands_first_vs_bands_last(self):
        """Test different band ordering options."""
        with patch('rasterio.open') as mock_rasterio:
            mock_dataset = Mock()
            mock_dataset.read.return_value = np.random.randint(
                1000, 5000, (4, 50, 50), dtype=np.uint16
            )
            mock_dataset.meta = {
                'width': 50, 'height': 50, 'count': 4, 'dtype': 'uint16'
            }
            mock_rasterio.return_value.__enter__.return_value = mock_dataset

            temp_file = Path(self.temp_dir) / "test.tif"
            temp_file.touch()

            # Test bands_last=True
            loader_bands_last = RasterImageLoader(bands_last=True)
            result_bands_last = loader_bands_last.load(str(temp_file))
            assert result_bands_last.shape == (50, 50, 4)

            # Test bands_last=False
            loader_bands_first = RasterImageLoader(bands_last=False)
            result_bands_first = loader_bands_first.load(str(temp_file))
            assert result_bands_first.shape == (4, 50, 50)

    @patch('rasterio.open')
    def test_preprocess_method_pipeline(self, mock_rasterio):
        """Test the _preprocess method pipeline."""
        loader = RasterImageLoader(
            auto_scale=True,
            convert_to_rrs=True,
            handle_nodata=True
        )

        # Test data with uint16 dtype
        raw_data = np.array([[[5000, 0, 3000]]], dtype=np.uint16)
        metadata = {'dtype': 'uint16', 'nodata': None}

        processed = loader._preprocess(raw_data, metadata)

        # Should be float32
        assert processed.dtype == np.float32

        # Should have scaled values (divided by 10000)
        assert np.isclose(processed[0, 0, 0], 0.5)  # 5000/10000
        assert np.isclose(processed[0, 0, 2], 0.3)  # 3000/10000

        # Zero should become NaN
        assert np.isnan(processed[0, 0, 1])


class TestIOIntegration:
    """Integration tests for IO modules."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_loader_preprocessor_integration(self):
        """Test integration between loader and preprocessor."""
        with patch('rasterio.open') as mock_rasterio:
            # Mock a realistic image
            raw_data = np.random.rand(4, 100, 100).astype(np.float32) * 0.1
            raw_data[:, 10:20, 10:20] = np.nan  # Add invalid area

            mock_dataset = Mock()
            mock_dataset.read.return_value = raw_data
            mock_dataset.meta = {
                'width': 100, 'height': 100, 'count': 4, 'dtype': 'float32'
            }
            mock_rasterio.return_value.__enter__.return_value = mock_dataset

            temp_file = Path(self.temp_dir) / "test.tif"
            temp_file.touch()

            # Load image
            loader = RasterImageLoader(bands_last=True)
            image_data = loader.load(str(temp_file))

            # Apply preprocessing
            water_mask = ImagePreprocessor.apply_water_mask(image_data)
            rgb_preview = ImagePreprocessor.create_rgb_preview(image_data)
            pixel_spectrum = ImagePreprocessor.extract_pixel_spectrum(image_data, 5, 5)

            # Verify integration works
            assert water_mask.shape == (100, 100)
            assert rgb_preview.shape == (100, 100, 3)
            assert pixel_spectrum.shape == (4,)

            # Invalid area should be masked out
            assert not water_mask[15, 15]  # Should be False due to NaN

    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        with patch('rasterio.open') as mock_rasterio:
            # Create realistic Sentinel-2 like data
            raw_data = np.random.randint(1000, 8000, (4, 50, 50), dtype=np.uint16)
            raw_data[0, 0:5, 0:5] = 0  # Land pixels
            raw_data[1, 45:50, 45:50] = 65535  # No-data

            mock_dataset = Mock()
            mock_dataset.read.return_value = raw_data
            mock_dataset.meta = {
                'width': 50, 'height': 50, 'count': 4,
                'dtype': 'uint16', 'nodata': None
            }
            mock_rasterio.return_value.__enter__.return_value = mock_dataset

            temp_file = Path(self.temp_dir) / "sentinel2.tif"
            temp_file.touch()

            # Complete workflow
            loader = RasterImageLoader(
                auto_scale=True,
                convert_to_rrs=True,
                handle_nodata=True,
                bands_last=True
            )

            # 1. Load and preprocess
            image_data = loader.load(str(temp_file))

            # 2. Create water mask
            water_mask = ImagePreprocessor.apply_water_mask(image_data)

            # 3. Generate RGB preview
            rgb_preview = ImagePreprocessor.create_rgb_preview(
                image_data, rgb_bands=(2, 1, 0)
            )

            # 4. Extract sample spectra
            valid_y, valid_x = np.where(water_mask)
            if len(valid_y) > 0:
                sample_spectrum = ImagePreprocessor.extract_pixel_spectrum(
                    image_data, valid_y[0], valid_x[0]
                )

                # Verify sample spectrum is valid
                assert len(sample_spectrum) == 4
                assert np.all(np.isfinite(sample_spectrum))
                assert np.all(sample_spectrum >= 0)
                assert np.all(sample_spectrum <= 1)  # Should be in reflectance units

            # Verify outputs
            assert image_data.shape == (50, 50, 4)
            assert water_mask.shape == (50, 50)
            assert rgb_preview.shape == (50, 50, 3)

            # Land and no-data areas should be masked
            assert not water_mask[2, 2]  # Land area
            assert not water_mask[47, 47]  # No-data area
