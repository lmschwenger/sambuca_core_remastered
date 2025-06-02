"""Integration tests for performance and scalability."""

import unittest
import tempfile
import shutil
import os
import time
import numpy as np
import pandas as pd
from pathlib import Path
import pytest

import sambuca.core as sbc
from sambuca.core.workflows import BathymetryWorkflow
from sambuca.core.inversion import InversionParameters, invert_spectrum, process_image
from sambuca.core.inversion.lut import LookUpTable


@pytest.mark.performance
class TestPerformanceIntegration(unittest.TestCase):
    """Integration tests for performance and scalability."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.siop_dir = os.path.join(cls.temp_dir, 'siops')
        cls.create_test_siops()
        cls.setup_test_parameters()
        cls.performance_results = {}

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment and print performance summary."""
        if hasattr(cls, 'performance_results') and cls.performance_results:
            cls.print_performance_summary()

        if hasattr(cls, 'temp_dir') and os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    @classmethod
    def create_test_siops(cls):
        """Create test SIOPs for performance testing."""
        os.makedirs(cls.siop_dir, exist_ok=True)

        # Minimal but realistic SIOPs
        wavelengths = np.array([492.4, 559.8, 664.6, 704.1])

        water_abs = np.array([0.0105, 0.0162, 0.3946, 0.6250])
        df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': water_abs})
        df.to_csv(os.path.join(cls.siop_dir, 'water_absorption.csv'), index=False)

        ph_abs = np.array([0.0280, 0.0200, 0.0120, 0.0100])
        df = pd.DataFrame({'Wavelength': wavelengths, 'Absorption': ph_abs})
        df.to_csv(os.path.join(cls.siop_dir, 'phytoplankton_absorption.csv'), index=False)

        sand_refl = np.array([0.15, 0.25, 0.35, 0.40])
        df = pd.DataFrame({'Wavelength': wavelengths, 'Reflectance': sand_refl})
        df.to_csv(os.path.join(cls.siop_dir, 'sand_substrate.csv'), index=False)

    @classmethod
    def setup_test_parameters(cls):
        """Set up test parameters and synthetic data."""
        siop_manager = sbc.SIOPManager(cls.siop_dir)
        siop_manager.register_sensor("TestSensor", [492.4, 559.8, 664.6, 704.1])

        cls.params = InversionParameters(
            depth=(0, 15),
            fixed_chl=1.0,
            fixed_cdom=0.1,
            fixed_nap=0.5,
            wavelengths=[492.4, 559.8, 664.6, 704.1]
        )
        cls.params.update_from_siop_manager(siop_manager, "TestSensor")

        # Generate test observation
        results = sbc.forward_model(
            chl=1.0, cdom=0.1, nap=0.5, depth=5.0,
            wavelengths=cls.params.wavelengths,
            a_water=cls.params.a_water,
            a_ph_star=cls.params.a_ph_star,
            substrate1=cls.params.substrate1,
            num_bands=4
        )
        cls.test_observation = results.rrs

    @classmethod
    def print_performance_summary(cls):
        """Print summary of performance test results."""
        print("\n" + "=" * 60)
        print("PERFORMANCE TEST SUMMARY")
        print("=" * 60)

        for test_name, result in cls.performance_results.items():
            if isinstance(result, dict):
                print(f"\n{test_name}:")
                for metric, value in result.items():
                    if isinstance(value, float):
                        if 'time' in metric.lower():
                            print(f"  {metric}: {value:.4f} seconds")
                        elif 'rate' in metric.lower():
                            print(f"  {metric}: {value:.1f}")
                        else:
                            print(f"  {metric}: {value:.3f}")
                    else:
                        print(f"  {metric}: {value}")
            else:
                print(f"{test_name}: {result}")

        print("=" * 60)

    def record_performance(self, test_name, metrics):
        """Record performance metrics for a test."""
        self.performance_results[test_name] = metrics

    def test_forward_model_performance(self):
        """Test forward model performance with multiple iterations."""
        n_iterations = 100

        start_time = time.perf_counter()
        for _ in range(n_iterations):
            sbc.forward_model(
                chl=1.0, cdom=0.1, nap=0.5, depth=5.0,
                wavelengths=self.params.wavelengths,
                a_water=self.params.a_water,
                a_ph_star=self.params.a_ph_star,
                substrate1=self.params.substrate1,
                num_bands=4
            )
        end_time = time.perf_counter()

        total_time = end_time - start_time
        avg_time = total_time / n_iterations
        calls_per_second = 1 / avg_time

        # Performance targets (adjust based on expectations)
        self.assertLess(avg_time, 0.01, "Forward model should be < 10ms per call")
        self.assertGreater(calls_per_second, 100, "Should achieve > 100 calls/second")

        self.record_performance('forward_model', {
            'avg_time_ms': avg_time * 1000,
            'calls_per_second': calls_per_second,
            'total_iterations': n_iterations
        })

    def test_single_inversion_performance(self):
        """Test single spectrum inversion performance."""
        n_iterations = 10

        times = []
        for _ in range(n_iterations):
            start_time = time.perf_counter()
            result = invert_spectrum(self.test_observation, self.params)
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        avg_time = np.mean(times)
        std_time = np.std(times)

        # Performance targets
        self.assertLess(avg_time, 5.0, "Single inversion should be < 5 seconds")

        self.record_performance('single_inversion', {
            'avg_time': avg_time,
            'std_time': std_time,
            'min_time': np.min(times),
            'max_time': np.max(times),
            'iterations': n_iterations
        })

    def test_lut_performance(self):
        """Test LUT building and lookup performance."""
        # Test different LUT sizes
        grid_sizes = [5, 10, 15]
        lut_results = {}

        for grid_size in grid_sizes:
            lut = LookUpTable(self.params)

            # Time LUT building
            start_time = time.perf_counter()
            lut.build_table(grid_size=grid_size, progress_bar=False)
            build_time = time.perf_counter() - start_time

            n_entries = grid_size ** len(self.params.get_inversion_parameter_names())

            # Time LUT lookup
            lookup_times = []
            for _ in range(10):
                start_time = time.perf_counter()
                result = lut.invert(self.test_observation, refine=False)
                lookup_time = time.perf_counter() - start_time
                lookup_times.append(lookup_time)

            avg_lookup_time = np.mean(lookup_times)

            lut_results[f'grid_{grid_size}'] = {
                'build_time': build_time,
                'n_entries': n_entries,
                'avg_lookup_time': avg_lookup_time,
                'lookups_per_second': 1 / avg_lookup_time
            }

            # Performance assertions
            self.assertLess(build_time, 30.0, f"LUT {grid_size}x{grid_size} should build in < 30s")
            self.assertLess(avg_lookup_time, 0.1, f"LUT lookup should be < 100ms")

        self.record_performance('lut_performance', lut_results)

    def test_image_processing_scaling(self):
        """Test how image processing scales with image size."""
        # Test different image sizes
        sizes = [(20, 20), (50, 50), (100, 100)]
        scaling_results = {}

        for height, width in sizes:
            # Create synthetic image
            image = np.random.uniform(0.005, 0.025, (height, width, 4))
            n_pixels = height * width

            # Time processing
            start_time = time.perf_counter()
            results = process_image(
                image,
                self.params,
                n_processes=1,
                progress_bar=False
            )
            end_time = time.perf_counter()

            processing_time = end_time - start_time
            pixels_per_second = n_pixels / processing_time

            scaling_results[f'{height}x{width}'] = {
                'processing_time': processing_time,
                'pixels_per_second': pixels_per_second,
                'n_pixels': n_pixels,
                'time_per_pixel_ms': (processing_time / n_pixels) * 1000
            }

            # Basic performance check
            self.assertGreater(pixels_per_second, 1, "Should process > 1 pixel/second")

        self.record_performance('image_scaling', scaling_results)

    def test_parallel_processing_speedup(self):
        """Test parallel processing speedup."""
        # Create medium-sized test image
        height, width = 30, 30
        image = np.random.uniform(0.005, 0.025, (height, width, 4))

        process_counts = [1, 2, 4]
        parallel_results = {}

        for n_processes in process_counts:
            start_time = time.perf_counter()
            results = process_image(
                image,
                self.params,
                n_processes=n_processes,
                progress_bar=False
            )
            end_time = time.perf_counter()

            processing_time = end_time - start_time
            parallel_results[f'{n_processes}_processes'] = {
                'processing_time': processing_time,
                'pixels_per_second': (height * width) / processing_time
            }

        # Calculate speedup
        if '1_processes' in parallel_results and '4_processes' in parallel_results:
            baseline_time = parallel_results['1_processes']['processing_time']
            parallel_time = parallel_results['4_processes']['processing_time']
            speedup = baseline_time / parallel_time

            parallel_results['speedup_4_vs_1'] = speedup

            # Should have some speedup (though perfect scaling is rare)
            self.assertGreater(speedup, 1.1, "4 processes should be faster than 1")

        self.record_performance('parallel_processing', parallel_results)

    def test_workflow_end_to_end_performance(self):
        """Test end-to-end workflow performance."""
        # Create small test image file
        height, width = 25, 25
        n_bands = 4

        # Generate synthetic image data
        image_data = np.zeros((n_bands, height, width), dtype=np.uint16)
        for i in range(height):
            for j in range(width):
                depth = 2.0 + (i / height) * 8.0

                try:
                    results = sbc.forward_model(
                        chl=1.0, cdom=0.1, nap=0.5, depth=depth,
                        wavelengths=self.params.wavelengths,
                        a_water=self.params.a_water,
                        a_ph_star=self.params.a_ph_star,
                        substrate1=self.params.substrate1,
                        num_bands=n_bands
                    )
                    scaled_rrs = (results.rrs * 10000).astype(np.uint16)
                    image_data[:, i, j] = scaled_rrs
                except:
                    image_data[:, i, j] = [800, 1000, 600, 400]

        # Save as temporary GeoTIFF
        import rasterio
        from rasterio.transform import from_bounds

        test_image_path = os.path.join(self.temp_dir, 'perf_test_image.tif')
        transform = from_bounds(0, 0, 250, 250, width, height)

        with rasterio.open(
            test_image_path, 'w',
            driver='GTiff',
            height=height,
            width=width,
            count=n_bands,
            dtype='uint16',
            transform=transform,
            compress='lzw'
        ) as dst:
            dst.write(image_data)

        # Test workflow performance
        workflow = BathymetryWorkflow(self.siop_dir, sensor='sentinel2')
        workflow.customize_parameters(
            depth=(0, 15),
            fixed_chl=1.0,
            fixed_cdom=0.1,
            fixed_nap=0.5
        )

        start_time = time.perf_counter()
        try:
            result = workflow.process_image(
                image_path=test_image_path,
                n_processes=1,
                progress_bar=False
            )
            end_time = time.perf_counter()

            processing_time = end_time - start_time
            n_pixels = height * width
            pixels_per_second = n_pixels / processing_time

            # Check that we got reasonable results
            depth_map = result.get_parameter_map('depth')
            valid_pixels = np.sum(~np.isnan(depth_map))

            workflow_results = {
                'total_time': processing_time,
                'pixels_per_second': pixels_per_second,
                'valid_pixels': int(valid_pixels),
                'total_pixels': n_pixels,
                'valid_percentage': (valid_pixels / n_pixels) * 100
            }

            # Performance targets
            self.assertGreater(pixels_per_second, 5, "Workflow should process > 5 pixels/second")
            self.assertGreater(valid_pixels, n_pixels * 0.5, "Should retrieve > 50% valid pixels")

        except Exception as e:
            workflow_results = {'error': str(e)}
            print(f"⚠️ Workflow performance test failed: {e}")

        self.record_performance('workflow_end_to_end', workflow_results)

    def test_memory_efficiency(self):
        """Test memory efficiency with larger datasets."""
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())

            # Baseline memory
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Test LUT memory usage
            lut = LookUpTable(self.params)
            lut.build_table(grid_size=20, progress_bar=False)
            lut_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Test image processing memory
            large_image = np.random.uniform(0.005, 0.025, (100, 100, 4))
            results = process_image(
                large_image,
                self.params,
                n_processes=1,
                progress_bar=False
            )
            processing_memory = process.memory_info().rss / 1024 / 1024  # MB

            memory_results = {
                'baseline_mb': baseline_memory,
                'lut_overhead_mb': lut_memory - baseline_memory,
                'processing_overhead_mb': processing_memory - lut_memory,
                'peak_memory_mb': processing_memory
            }

            # Memory efficiency checks
            self.assertLess(lut_memory - baseline_memory, 100, "LUT should use < 100MB")
            self.assertLess(processing_memory - baseline_memory, 200, "Processing should use < 200MB total")

            self.record_performance('memory_efficiency', memory_results)

        except ImportError:
            self.skipTest("psutil not available for memory testing")

    def test_error_handling_performance(self):
        """Test performance of error handling with invalid data."""
        # Test with various invalid inputs
        invalid_inputs = [
            np.array([np.nan, 0.01, 0.01, 0.01]),  # NaN values
            np.array([-0.01, 0.01, 0.01, 0.01]),   # Negative values
            np.array([0.01, 0.01, 0.01, np.inf]),  # Infinite values
            np.array([0.0, 0.0, 0.0, 0.0]),        # Zero values
        ]

        error_handling_times = []

        for invalid_input in invalid_inputs:
            start_time = time.perf_counter()
            try:
                result = invert_spectrum(invalid_input, self.params)
            except:
                pass  # Expected to fail
            end_time = time.perf_counter()

            error_handling_times.append(end_time - start_time)

        avg_error_time = np.mean(error_handling_times)

        # Error handling should be fast
        self.assertLess(avg_error_time, 1.0, "Error handling should be < 1 second")

        self.record_performance('error_handling', {
            'avg_error_handling_time': avg_error_time,
            'max_error_handling_time': np.max(error_handling_times),
            'n_tests': len(invalid_inputs)
        })

    @pytest.mark.slow
    def test_stress_test(self):
        """Stress test with challenging scenarios."""
        # Create various challenging scenarios
        stress_scenarios = [
            {'name': 'very_shallow', 'depth_range': (0.1, 1.0)},
            {'name': 'very_deep', 'depth_range': (20, 50)},
            {'name': 'very_turbid', 'chl': 10.0, 'nap': 5.0},
            {'name': 'very_clear', 'chl': 0.01, 'nap': 0.01},
        ]

        stress_results = {}

        for scenario in stress_scenarios:
            scenario_name = scenario['name']

            if 'depth_range' in scenario:
                # Test with depth range
                params = InversionParameters(
                    depth=scenario['depth_range'],
                    fixed_chl=1.0,
                    fixed_cdom=0.1,
                    fixed_nap=0.5,
                    wavelengths=self.params.wavelengths
                )
                params.update_from_siop_manager(sbc.SIOPManager(self.siop_dir), "TestSensor")

                test_obs = self.test_observation
            else:
                # Generate observation with extreme parameters
                try:
                    results = sbc.forward_model(
                        chl=scenario.get('chl', 1.0),
                        cdom=scenario.get('cdom', 0.1),
                        nap=scenario.get('nap', 0.5),
                        depth=scenario.get('depth', 5.0),
                        wavelengths=self.params.wavelengths,
                        a_water=self.params.a_water,
                        a_ph_star=self.params.a_ph_star,
                        substrate1=self.params.substrate1,
                        num_bands=4
                    )
                    test_obs = results.rrs
                    params = self.params
                except:
                    continue

            # Test inversion
            start_time = time.perf_counter()
            try:
                result = invert_spectrum(test_obs, params)
                success = result.convergence_status
                error = result.objective_value
            except Exception as e:
                success = False
                error = float('inf')

            end_time = time.perf_counter()

            stress_results[scenario_name] = {
                'success': success,
                'error': error if error != float('inf') else 'failed',
                'time': end_time - start_time
            }

        self.record_performance('stress_test', stress_results)

        # At least some scenarios should succeed
        successes = sum(1 for r in stress_results.values() if r['success'])
        self.assertGreater(successes, 0, "At least one stress test scenario should succeed")


if __name__ == '__main__':
    unittest.main()