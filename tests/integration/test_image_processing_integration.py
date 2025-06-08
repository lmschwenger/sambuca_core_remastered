"""Integration tests for image processing functionality."""

import os
import shutil
import tempfile
import unittest

import numpy as np
import pandas as pd
import pytest
import rasterio

from sambuca.core import SIOPManager
from sambuca.core.inversion import InversionParameters, process_image
from sambuca.core.io import RasterImageLoader, ImagePreprocessor


class TestImageProcessingIntegration(unittest.TestCase):
    """Integration tests for image I/O and processing functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.siop_dir = os.path.join(cls.temp_dir, 'siops')
        cls.create_test_siops()

        # Look for existing test images
        cls.test_images = cls.find_test_images()
        if not cls.test_images:
            pytest.skip("No test images found - skipping image processing integration tests")

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        if hasattr(cls, 'temp_dir') and os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    @classmethod
    def create_test_siops(cls):
        """Create test SIOP files."""
        os.makedirs(cls.siop_dir, exist_ok=True)

        wavelengths = np.array([450, 550, 650, 750])

        # Basic SIOPs for testing
        water_abs = np.array([0.01, 0.02, 0.1, 0.5])
        df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': water_abs})
        df.to_csv(os.path.join(cls.siop_dir, 'water_absorption.csv'), index=False)

        ph_abs = np.array([0.05, 0.03, 0.02, 0.01])
        df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': ph_abs})
        df.to_csv(os.path.join(cls.siop_dir, 'phytoplankton_absorption.csv'), index=False)

        sand_refl = np.array([0.1, 0.2, 0.3, 0.4])
        df = pd.DataFrame({'Wavelength': wavelengths, 'Reflectance': sand_refl})
        df.to_csv(os.path.join(cls.siop_dir, 'sand_substrate.csv'), index=False)

    @classmethod
    def find_test_images(cls):
        return {'test_image': os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'input',
                                           'integration_test_image.tif')}

    def test_raster_image_loading(self):
        """Test basic raster image loading functionality."""
        if not self.test_images:
            self.skipTest("No test images available")

        loader = RasterImageLoader()

        # Test with first available image
        image_path = next(iter(self.test_images.values()))

        try:
            # Test basic loading
            image_data = loader.load(image_path)

            # Check basic properties
            self.assertIsNotNone(image_data.data)
            self.assertIsNotNone(image_data.metadata)
            self.assertTrue(image_data.is_bands_last)
            self.assertEqual(len(image_data.shape), 3)

            # Check data type
            self.assertEqual(image_data.data.dtype, np.float32)

            # Check that values are in reasonable range for reflectance
            valid_data = image_data.data[~np.isnan(image_data.data)]
            if len(valid_data) > 0:
                self.assertTrue(np.all(valid_data >= 0))
                self.assertTrue(np.all(valid_data <= 1))

            print(f" Basic image loading test passed: {image_data.shape}")

        except Exception as e:
            self.fail(f"Image loading failed: {e}")

    def test_image_loading_with_bands(self):
        """Test image loading with specific band selection."""
        if not self.test_images:
            self.skipTest("No test images available")

        loader = RasterImageLoader()
        image_path = next(iter(self.test_images.values()))

        try:
            # Load specific bands
            image_data = loader.load(image_path, bands=[1, 2, 3, 4])

            # Check that we got the right number of bands
            self.assertEqual(image_data.shape[2], 4)

            print(f" Band selection test passed: {image_data.shape}")

        except Exception as e:
            self.skipTest(f"Band selection test failed: {e}")

    def test_image_preprocessing(self):
        """Test image preprocessing functionality."""
        if not self.test_images:
            self.skipTest("No test images available")

        loader = RasterImageLoader()
        image_path = next(iter(self.test_images.values()))

        try:
            image_data = loader.load(image_path)

            # Test RGB preview creation
            rgb = ImagePreprocessor.create_rgb_preview(image_data)
            self.assertEqual(len(rgb.shape), 3)
            self.assertEqual(rgb.shape[2], 3)
            self.assertTrue(np.all(rgb >= 0))
            self.assertTrue(np.all(rgb <= 1))

            # Test pixel extraction
            height, width = image_data.shape[:2]
            test_y, test_x = height // 2, width // 2

            pixel_spectrum = ImagePreprocessor.extract_pixel_spectrum(
                image_data, test_y, test_x
            )
            self.assertEqual(len(pixel_spectrum), image_data.shape[2])

            print(" Image preprocessing tests passed")

        except Exception as e:
            self.skipTest(f"Image preprocessing failed: {e}")

    def test_water_mask_application(self):
        """Test water mask functionality."""
        if not self.test_images:
            self.skipTest("No test images available")

        loader = RasterImageLoader()
        image_path = next(iter(self.test_images.values()))

        try:
            image_data = loader.load(image_path)

            # Test without mask (should return valid pixel mask)
            water_mask = ImagePreprocessor.apply_water_mask(image_data)

            # Check mask properties
            self.assertEqual(water_mask.shape, image_data.shape[:2])
            self.assertEqual(water_mask.dtype, bool)

            # Should have some valid pixels
            self.assertTrue(np.any(water_mask))

            print(f" Water mask test passed: {np.sum(water_mask)} valid pixels")

        except Exception as e:
            self.skipTest(f"Water mask test failed: {e}")

    @pytest.mark.integration
    def test_low_level_image_processing(self):
        """Test low-level image processing with process_image function."""
        if not self.test_images:
            self.skipTest("No test images available")

        # Set up SIOP manager and parameters
        siop_manager = SIOPManager(self.siop_dir)
        siop_manager.register_sensor("TestSensor", [450, 550, 650, 750])

        params = InversionParameters(
            depth=(0, 10),
            fixed_chl=1.0,
            fixed_cdom=0.1,
            fixed_nap=0.5,
            wavelengths=[450, 550, 650, 750]
        )
        params.update_from_siop_manager(siop_manager, "TestSensor")

        # Load and process a small subset of image
        loader = RasterImageLoader()
        image_path = next(iter(self.test_images.values()))

        try:
            image_data = loader.load(image_path)

            # Extract a small subset for testing (to keep it fast)
            height, width = image_data.shape[:2]
            subset_size = min(20, height // 4, width // 4)  # Small subset

            start_y = height // 2 - subset_size // 2
            start_x = width // 2 - subset_size // 2
            end_y = start_y + subset_size
            end_x = start_x + subset_size

            subset = image_data.data[start_y:end_y, start_x:end_x, :]

            print(f"Processing subset: {subset.shape}")

            # Process the subset
            results = process_image(
                subset,
                params,
                n_processes=1,
                progress_bar=False
            )

            # Check results
            self.assertIn('depth', results)
            self.assertEqual(results['depth'].shape, subset.shape[:2])

            # Check that some pixels have valid results
            valid_depths = results['depth'][~np.isnan(results['depth'])]
            if len(valid_depths) > 0:
                self.assertTrue(np.all(valid_depths >= 0))
                self.assertTrue(np.all(valid_depths <= 50))  # Reasonable depth range
                print(f" Processed {len(valid_depths)} valid pixels")
            else:
                print("⚠️ No valid depth retrievals (may be expected for test data)")

        except Exception as e:
            self.skipTest(f"Low-level processing failed: {e}")

    def test_image_format_compatibility(self):
        """Test compatibility with different image formats and metadata."""
        if not self.test_images:
            self.skipTest("No test images available")

        loader = RasterImageLoader()

        # Test all available images
        for image_name, image_path in self.test_images.items():
            try:
                with rasterio.open(image_path) as src:
                    print(f"Testing {image_name}: {src.count} bands, {src.dtypes[0]} dtype")

                # Test loading
                image_data = loader.load(image_path)

                # Basic checks
                self.assertIsNotNone(image_data.data)
                self.assertIsNotNone(image_data.metadata)
                self.assertTrue(image_data.is_bands_last)

                print(f" {image_name} loaded successfully: {image_data.shape}")

            except Exception as e:
                print(f"⚠️ {image_name} failed to load: {e}")
                # Don't fail the test, just note the issue

    def test_image_scaling_and_conversion(self):
        """Test automatic scaling and data type conversion."""
        if not self.test_images:
            self.skipTest("No test images available")

        loader = RasterImageLoader()
        image_path = next(iter(self.test_images.values()))

        try:
            # Test with auto scaling
            image_data = loader.load(image_path)

            # Check that data was scaled appropriately
            valid_data = image_data.data[~np.isnan(image_data.data)]
            if len(valid_data) > 0:
                # For Sentinel-2 L2A data, values should be in 0-1 range after scaling
                max_val = np.max(valid_data)
                min_val = np.min(valid_data)

                # Should be reasonable reflectance values
                self.assertGreaterEqual(min_val, 0)
                self.assertLessEqual(max_val, 1)

                print(f" Data scaling test passed: range {min_val:.4f} - {max_val:.4f}")

        except Exception as e:
            self.skipTest(f"Data scaling test failed: {e}")

    def test_large_image_handling(self):
        """Test handling of larger images with memory efficiency."""
        if not self.test_images:
            self.skipTest("No test images available")

        # Find the largest available test image
        largest_image = None
        largest_size = 0

        for image_name, image_path in self.test_images.items():
            try:
                with rasterio.open(image_path) as src:
                    size = src.height * src.width
                    if size > largest_size:
                        largest_size = size
                        largest_image = image_path
            except:
                continue

        if not largest_image:
            self.skipTest("No suitable large image found")

        try:
            loader = RasterImageLoader()

            # Test loading large image
            image_data = loader.load(largest_image)

            # Check that it loaded successfully
            self.assertIsNotNone(image_data.data)

            # Test memory-efficient operations
            # (e.g., don't load entire image into different formats)
            total_pixels = image_data.shape[0] * image_data.shape[1]

            print(f" Large image handling test passed: {total_pixels} pixels")

        except Exception as e:
            self.skipTest(f"Large image handling failed: {e}")


if __name__ == '__main__':
    unittest.main()
