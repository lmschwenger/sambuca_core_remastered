#!/usr/bin/env python3
"""
Performance Benchmarks for Sambuca Core
=======================================

This module provides performance benchmarks and timing tests for the sambuca_core package.
It helps identify bottlenecks and track performance improvements over time.
"""

import cProfile
import io
import pstats
import time
from contextlib import contextmanager

import matplotlib.pyplot as plt
import numpy as np

import sambuca_core as sbc
from sambuca_core.inversion import InversionParameters, invert_spectrum, multi_start_inversion
from sambuca_core.inversion.lut import LookUpTable


class PerformanceBenchmark:
    """Performance benchmark suite for Sambuca Core."""

    def __init__(self):
        """Initialize the benchmark suite."""
        self.results = {}
        self.setup_test_data()

    def setup_test_data(self):
        """Set up test data for benchmarks."""
        # Standard test wavelengths (Sentinel-2)
        self.wavelengths = np.array([492.4, 559.8, 664.6, 704.1])
        self.num_bands = len(self.wavelengths)

        # Standard SIOPs
        self.a_water = np.array([0.0105, 0.0162, 0.3946, 0.6250])
        self.a_ph_star = np.array([0.0280, 0.0200, 0.0120, 0.0100])
        self.substrate1 = np.array([0.15, 0.25, 0.35, 0.40])

        # Generate synthetic observed data
        self.observed_rrs = self._generate_test_spectrum()

        # Standard inversion parameters
        self.inversion_params = InversionParameters(
            chl=(0.1, 10.0),
            cdom=(0.01, 1.0),
            nap=(0.1, 5.0),
            depth=(0.5, 15.0),
            wavelengths=self.wavelengths,
            a_water=self.a_water,
            a_ph_star=self.a_ph_star,
            substrate1=self.substrate1
        )

    def _generate_test_spectrum(self):
        """Generate a test spectrum for benchmarking."""
        results = sbc.forward_model(
            chl=2.0, cdom=0.1, nap=1.0, depth=5.0,
            wavelengths=self.wavelengths,
            a_water=self.a_water,
            a_ph_star=self.a_ph_star,
            substrate1=self.substrate1,
            num_bands=self.num_bands
        )
        return results.rrs

    @contextmanager
    def timer(self, name: str):
        """Context manager for timing operations."""
        start_time = time.perf_counter()
        yield
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        self.results[name] = elapsed
        print(f"{name}: {elapsed:.4f} seconds")

    def benchmark_forward_model(self, iterations: int = 1000):
        """Benchmark forward model performance."""
        print(f"\nBenchmarking Forward Model ({iterations} iterations)...")

        # Single iteration timing
        with self.timer("forward_model_single"):
            sbc.forward_model(
                chl=2.0, cdom=0.1, nap=1.0, depth=5.0,
                wavelengths=self.wavelengths,
                a_water=self.a_water,
                a_ph_star=self.a_ph_star,
                substrate1=self.substrate1,
                num_bands=self.num_bands
            )

        # Multiple iterations timing
        start_time = time.perf_counter()
        for _ in range(iterations):
            sbc.forward_model(
                chl=2.0, cdom=0.1, nap=1.0, depth=5.0,
                wavelengths=self.wavelengths,
                a_water=self.a_water,
                a_ph_star=self.a_ph_star,
                substrate1=self.substrate1,
                num_bands=self.num_bands
            )
        end_time = time.perf_counter()

        total_time = end_time - start_time
        avg_time = total_time / iterations

        self.results[f"forward_model_{iterations}_avg"] = avg_time
        self.results[f"forward_model_{iterations}_total"] = total_time

        print(f"Average time per call: {avg_time * 1000:.2f} ms")
        print(f"Calls per second: {1 / avg_time:.0f}")

    def benchmark_inversion_methods(self):
        """Benchmark different inversion methods."""
        print("\nBenchmarking Inversion Methods...")

        # Single optimization
        with self.timer("inversion_single"):
            result = invert_spectrum(self.observed_rrs, self.inversion_params)

        # Multi-start optimization (3 starts)
        with self.timer("inversion_multi_3"):
            result = multi_start_inversion(
                self.observed_rrs, self.inversion_params, n_starts=3
            )

        # Multi-start optimization (5 starts)
        with self.timer("inversion_multi_5"):
            result = multi_start_inversion(
                self.observed_rrs, self.inversion_params, n_starts=5
            )

    def benchmark_lut_operations(self):
        """Benchmark Look-Up Table operations."""
        print("\nBenchmarking LUT Operations...")

        # LUT creation with different grid sizes
        grid_sizes = [5, 10, 15, 20]

        for grid_size in grid_sizes:
            lut = LookUpTable(self.inversion_params)

            with self.timer(f"lut_build_{grid_size}x{grid_size}"):
                lut.build_table(grid_size=grid_size, progress_bar=False)

            # LUT inversion (no refinement)
            with self.timer(f"lut_invert_{grid_size}x{grid_size}_no_refine"):
                result = lut.invert(self.observed_rrs, refine=False)

            # LUT inversion (with refinement)
            with self.timer(f"lut_invert_{grid_size}x{grid_size}_refine"):
                result = lut.invert(self.observed_rrs, refine=True)

            print(f"LUT {grid_size}x{grid_size}: {grid_size ** 2} entries")

    def benchmark_scaling(self):
        """Benchmark how performance scales with problem size."""
        print("\nBenchmarking Scaling Performance...")

        # Test different numbers of spectral bands
        band_counts = [3, 4, 6, 8, 10]

        for n_bands in band_counts:
            # Create test data with n_bands
            test_wavelengths = np.linspace(400, 800, n_bands)
            test_a_water = np.linspace(0.01, 0.5, n_bands)
            test_a_ph_star = np.linspace(0.05, 0.01, n_bands)
            test_substrate1 = np.linspace(0.1, 0.4, n_bands)

            # Time forward model
            start_time = time.perf_counter()
            for _ in range(100):  # Average over multiple runs
                sbc.forward_model(
                    chl=2.0, cdom=0.1, nap=1.0, depth=5.0,
                    wavelengths=test_wavelengths,
                    a_water=test_a_water,
                    a_ph_star=test_a_ph_star,
                    substrate1=test_substrate1,
                    num_bands=n_bands
                )
            end_time = time.perf_counter()

            avg_time = (end_time - start_time) / 100
            self.results[f"forward_model_{n_bands}_bands"] = avg_time
            print(f"{n_bands} bands: {avg_time * 1000:.2f} ms per call")

    def profile_inversion(self):
        """Profile inversion to identify bottlenecks."""
        print("\nProfiling Inversion Performance...")

        pr = cProfile.Profile()
        pr.enable()

        # Run inversion multiple times for better profiling data
        for _ in range(10):
            invert_spectrum(self.observed_rrs, self.inversion_params)

        pr.disable()

        # Analyze profiling results
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions

        profile_output = s.getvalue()
        print("Top 20 functions by cumulative time:")
        print(profile_output)

        # Save detailed profile to file
        with open('inversion_profile.txt', 'w') as f:
            f.write(profile_output)

        print("Detailed profile saved to 'inversion_profile.txt'")

    def benchmark_memory_usage(self):
        """Benchmark memory usage of different operations."""
        print("\nBenchmarking Memory Usage...")

        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())

            # Baseline memory
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Memory usage for LUT creation
            lut = LookUpTable(self.inversion_params)
            lut.build_table(grid_size=20, progress_bar=False)
            lut_memory = process.memory_info().rss / 1024 / 1024  # MB

            print(f"Baseline memory: {baseline_memory:.1f} MB")
            print(f"LUT memory: {lut_memory:.1f} MB")
            print(f"LUT overhead: {lut_memory - baseline_memory:.1f} MB")

            self.results['memory_baseline'] = baseline_memory
            self.results['memory_lut_20x20'] = lut_memory

        except ImportError:
            print("psutil not available for memory profiling")

    def create_performance_report(self):
        """Create a comprehensive performance report."""
        print("\n" + "=" * 60)
        print("PERFORMANCE REPORT")
        print("=" * 60)

        # Forward model performance
        if 'forward_model_single' in self.results:
            print(f"\nForward Model:")
            print(f"  Single call: {self.results['forward_model_single'] * 1000:.2f} ms")

            if 'forward_model_1000_avg' in self.results:
                avg_ms = self.results['forward_model_1000_avg'] * 1000
                calls_per_sec = 1 / self.results['forward_model_1000_avg']
                print(f"  Average (1000 calls): {avg_ms:.2f} ms")
                print(f"  Throughput: {calls_per_sec:.0f} calls/second")

        # Inversion performance
        print(f"\nInversion Methods:")
        for method in ['single', 'multi_3', 'multi_5']:
            key = f'inversion_{method}'
            if key in self.results:
                print(f"  {method.replace('_', ' ').title()}: {self.results[key]:.2f} seconds")

        # LUT performance
        print(f"\nLUT Performance:")
        lut_build_times = {k: v for k, v in self.results.items() if k.startswith('lut_build_')}
        for grid_key in sorted(lut_build_times.keys()):
            grid_size = grid_key.split('_')[2]
            build_time = lut_build_times[grid_key]
            print(f"  Build {grid_size}: {build_time:.2f} seconds")

        # Scaling performance
        print(f"\nScaling (Forward Model):")
        scaling_times = {k: v for k, v in self.results.items() if
                         k.startswith('forward_model_') and k.endswith('_bands')}
        for band_key in sorted(scaling_times.keys(), key=lambda x: int(x.split('_')[2])):
            n_bands = band_key.split('_')[2]
            avg_time = scaling_times[band_key] * 1000
            print(f"  {n_bands} bands: {avg_time:.2f} ms")

        print("=" * 60)

    def plot_performance_results(self):
        """Create performance visualization plots."""
        print("\nCreating performance plots...")

        fig, axes = plt.subplots(2, 2, figsize=(15, 12))

        # Plot 1: Inversion method comparison
        ax1 = axes[0, 0]
        inversion_methods = []
        inversion_times = []

        for method in ['single', 'multi_3', 'multi_5']:
            key = f'inversion_{method}'
            if key in self.results:
                inversion_methods.append(method.replace('_', ' ').title())
                inversion_times.append(self.results[key])

        if inversion_times:
            bars = ax1.bar(inversion_methods, inversion_times)
            ax1.set_ylabel('Time (seconds)')
            ax1.set_title('Inversion Method Performance')
            ax1.grid(True, alpha=0.3)

            # Add value labels on bars
            for bar, time_val in zip(bars, inversion_times):
                ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                         f'{time_val:.2f}s', ha='center', va='bottom')

        # Plot 2: LUT build time vs grid size
        ax2 = axes[0, 1]
        grid_sizes = []
        build_times = []

        for key, value in self.results.items():
            if key.startswith('lut_build_') and 'x' in key:
                grid_size = int(key.split('_')[2].split('x')[0])
                grid_sizes.append(grid_size)
                build_times.append(value)

        if grid_sizes:
            sorted_data = sorted(zip(grid_sizes, build_times))
            grid_sizes, build_times = zip(*sorted_data)

            ax2.plot(grid_sizes, build_times, 'o-', linewidth=2, markersize=8)
            ax2.set_xlabel('Grid Size (per dimension)')
            ax2.set_ylabel('Build Time (seconds)')
            ax2.set_title('LUT Build Time vs Grid Size')
            ax2.grid(True, alpha=0.3)

        # Plot 3: Forward model scaling
        ax3 = axes[1, 0]
        band_counts = []
        scaling_times = []

        for key, value in self.results.items():
            if key.startswith('forward_model_') and key.endswith('_bands'):
                n_bands = int(key.split('_')[2])
                band_counts.append(n_bands)
                scaling_times.append(value * 1000)  # Convert to ms

        if band_counts:
            sorted_data = sorted(zip(band_counts, scaling_times))
            band_counts, scaling_times = zip(*sorted_data)

            ax3.plot(band_counts, scaling_times, 'o-', linewidth=2, markersize=8)
            ax3.set_xlabel('Number of Spectral Bands')
            ax3.set_ylabel('Time per Call (ms)')
            ax3.set_title('Forward Model Scaling')
            ax3.grid(True, alpha=0.3)

        # Plot 4: Memory usage (if available)
        ax4 = axes[1, 1]
        if 'memory_baseline' in self.results and 'memory_lut_20x20' in self.results:
            memory_types = ['Baseline', 'LUT (20x20)']
            memory_values = [
                self.results['memory_baseline'],
                self.results['memory_lut_20x20']
            ]

            bars = ax4.bar(memory_types, memory_values)
            ax4.set_ylabel('Memory Usage (MB)')
            ax4.set_title('Memory Usage Comparison')
            ax4.grid(True, alpha=0.3)

            # Add value labels
            for bar, mem_val in zip(bars, memory_values):
                ax4.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                         f'{mem_val:.1f} MB', ha='center', va='bottom')
        else:
            ax4.text(0.5, 0.5, 'Memory profiling\nnot available',
                     ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Memory Usage')

        plt.tight_layout()
        plt.savefig('performance_benchmarks.png', dpi=300, bbox_inches='tight')
        plt.show()

        print("Performance plots saved as 'performance_benchmarks.png'")

    def run_full_benchmark(self):
        """Run the complete benchmark suite."""
        print("SAMBUCA CORE PERFORMANCE BENCHMARK SUITE")
        print("=" * 60)

        # Run all benchmarks
        self.benchmark_forward_model(iterations=1000)
        self.benchmark_inversion_methods()
        self.benchmark_lut_operations()
        self.benchmark_scaling()
        self.benchmark_memory_usage()

        # Generate reports
        self.create_performance_report()
        self.plot_performance_results()

        # Optional detailed profiling
        response = input("\nRun detailed profiling? (y/n): ")
        if response.lower() == 'y':
            self.profile_inversion()

        print("\nBenchmark suite completed!")


def compare_optimization_methods():
    """Compare different optimization methods for inversion."""
    print("\nComparing Optimization Methods...")

    # Set up test data
    wavelengths = np.array([450, 550, 650, 750])
    a_water = np.array([0.01, 0.02, 0.1, 0.5])
    a_ph_star = np.array([0.05, 0.03, 0.02, 0.01])
    substrate1 = np.array([0.1, 0.2, 0.3, 0.4])

    # Generate synthetic observation
    results = sbc.forward_model(
        chl=2.0, cdom=0.1, nap=1.0, depth=5.0,
        wavelengths=wavelengths,
        a_water=a_water,
        a_ph_star=a_ph_star,
        substrate1=substrate1,
        num_bands=len(wavelengths)
    )
    observed_rrs = results.rrs

    # Set up inversion parameters
    inversion_params = InversionParameters(
        chl=(0.1, 10.0),
        cdom=(0.01, 1.0),
        nap=(0.1, 5.0),
        depth=(0.5, 15.0),
        wavelengths=wavelengths,
        a_water=a_water,
        a_ph_star=a_ph_star,
        substrate1=substrate1
    )

    # Test different optimization methods
    methods = ['L-BFGS-B', 'TNC', 'SLSQP']

    print(f"{'Method':<12} {'Time (s)':<10} {'Error':<12} {'Success':<8}")
    print("-" * 45)

    for method in methods:
        start_time = time.perf_counter()
        try:
            result = invert_spectrum(
                observed_rrs, inversion_params, method=method
            )
            end_time = time.perf_counter()

            elapsed = end_time - start_time
            error = result.objective_value
            success = result.convergence_status

            print(f"{method:<12} {elapsed:<10.3f} {error:<12.6f} {success}")

        except Exception as e:
            print(f"{method:<12} {'FAILED':<10} {str(e)[:12]:<12} {'False'}")


def run_stress_test():
    """Run stress tests with challenging scenarios."""
    print("\nRunning Stress Tests...")

    # Set up test scenario
    wavelengths = np.array([450, 550, 650, 750])
    a_water = np.array([0.01, 0.02, 0.1, 0.5])
    a_ph_star = np.array([0.05, 0.03, 0.02, 0.01])
    substrate1 = np.array([0.1, 0.2, 0.3, 0.4])

    inversion_params = InversionParameters(
        chl=(0.1, 10.0),
        cdom=(0.01, 1.0),
        nap=(0.1, 5.0),
        depth=(0.5, 15.0),
        wavelengths=wavelengths,
        a_water=a_water,
        a_ph_star=a_ph_star,
        substrate1=substrate1
    )

    # Generate challenging test cases
    test_cases = [
        # Very turbid water
        {'chl': 8.0, 'cdom': 0.8, 'nap': 4.0, 'depth': 1.0},
        # Very clear water
        {'chl': 0.1, 'cdom': 0.01, 'nap': 0.1, 'depth': 15.0},
        # Deep water
        {'chl': 1.0, 'cdom': 0.1, 'nap': 0.5, 'depth': 50.0},
        # High CDOM
        {'chl': 0.5, 'cdom': 1.0, 'nap': 0.2, 'depth': 5.0},
    ]

    print(f"{'Scenario':<15} {'Time (s)':<10} {'Error':<12} {'Success':<8}")
    print("-" * 50)

    for i, case in enumerate(test_cases, 1):
        # Generate observation
        results = sbc.forward_model(
            **case,
            wavelengths=wavelengths,
            a_water=a_water,
            a_ph_star=a_ph_star,
            substrate1=substrate1,
            num_bands=len(wavelengths)
        )

        # Add noise
        noise = np.random.normal(0, 0.001, len(results.rrs))
        observed_rrs = results.rrs + noise

        # Time inversion
        start_time = time.perf_counter()
        try:
            result = multi_start_inversion(
                observed_rrs, inversion_params, n_starts=5
            )
            end_time = time.perf_counter()

            elapsed = end_time - start_time
            error = result.objective_value
            success = result.convergence_status

            scenario_name = f"Case {i}"
            print(f"{scenario_name:<15} {elapsed:<10.3f} {error:<12.6f} {success}")

        except Exception as e:
            print(f"Case {i:<15} {'FAILED':<10} {str(e)[:12]:<12} {'False'}")


if __name__ == "__main__":
    # Run the main benchmark suite
    benchmark = PerformanceBenchmark()
    benchmark.run_full_benchmark()

    # Run additional tests
    compare_optimization_methods()
    run_stress_test()

    print("\nAll performance tests completed!")
