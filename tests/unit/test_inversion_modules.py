"""Unit tests for sambuca.core.inversion modules."""

import shutil
import tempfile
from unittest.mock import Mock, patch

import numpy as np
import pytest

from sambuca.core.inversion.lut import LookUpTable
from sambuca.core.inversion.objective_functions import (
    SpectralRMSE,
    SpectralAngleMapper,
    SpectralRelativeRMSE,
    SpectralChiSquare,
    SpectralRMSEWithNEDR,
    create_rmse,
    create_angle_mapper,
    create_relative_rmse,
    create_chi_square,
    create_rmse_with_nedr
)
from sambuca.core.inversion.optimization import invert_spectrum, multi_start_inversion
from sambuca.core.inversion.optimization_result import OptimizationResult
from sambuca.core.inversion.parameters import InversionParameters
from sambuca.core.inversion.pixel_processor import process_pixel, process_image


class TestInversionParameters:
    """Test InversionParameters functionality."""

    def test_initialization_defaults(self):
        """Test default initialization."""
        params = InversionParameters()

        assert params.chl is None
        assert params.cdom is None
        assert params.nap is None
        assert params.depth is None
        assert params.substrate_fraction is None

        assert params.fixed_chl == 1.0
        assert params.fixed_cdom == 0.5
        assert params.fixed_nap == 1.0
        assert params.fixed_depth == 5.0
        assert params.fixed_substrate_fraction == 1.0

    def test_initialization_with_bounds(self):
        """Test initialization with parameter bounds."""
        params = InversionParameters(
            chl=(0.1, 10.0),
            depth=(0.5, 30.0),
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )

        assert params.chl == (0.1, 10.0)
        assert params.depth == (0.5, 30.0)
        assert len(params.wavelengths) == 4
        assert len(params.a_water) == 4

    def test_get_parameter_bounds(self):
        """Test getting parameter bounds."""
        params = InversionParameters(
            chl=(0.1, 10.0),
            cdom=(0.001, 0.1),
            depth=(0.5, 30.0)
        )

        bounds = params.get_parameter_bounds()
        expected = [(0.1, 10.0), (0.001, 0.1), (0.5, 30.0)]
        assert bounds == expected

    def test_get_parameter_bounds_empty(self):
        """Test getting bounds when no parameters are set for inversion."""
        params = InversionParameters()
        bounds = params.get_parameter_bounds()
        assert bounds == []

    def test_get_inversion_parameter_names(self):
        """Test getting names of parameters being inverted."""
        params = InversionParameters(
            chl=(0.1, 10.0),
            depth=(0.5, 30.0),
            substrate_fraction=(0.0, 1.0)
        )

        names = params.get_inversion_parameter_names()
        expected = ['chl', 'depth', 'substrate_fraction']
        assert names == expected

    def test_get_initial_values(self):
        """Test getting initial values from bounds midpoints."""
        params = InversionParameters(
            chl=(0.1, 10.0),
            cdom=(0.001, 0.1)
        )

        initial = params.get_initial_values()
        expected = [5.05, 0.0505]  # Midpoints
        assert np.allclose(initial, expected)

    def test_get_forward_model_params_no_inversion(self):
        """Test forward model params when no parameters are being inverted."""
        params = InversionParameters(
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )

        fwd_params = params.get_forward_model_params([])

        assert fwd_params['chl'] == params.fixed_chl
        assert fwd_params['cdom'] == params.fixed_cdom
        assert fwd_params['depth'] == params.fixed_depth
        assert fwd_params['wavelengths'] == params.wavelengths
        assert fwd_params['num_bands'] == 4

    def test_get_forward_model_params_with_inversion(self):
        """Test forward model params with parameters being inverted."""
        params = InversionParameters(
            chl=(0.1, 10.0),
            depth=(0.5, 30.0),
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )

        # Test with inversion parameter values
        x = [2.5, 15.0]  # chl=2.5, depth=15.0
        fwd_params = params.get_forward_model_params(x)

        assert fwd_params['chl'] == 2.5
        assert fwd_params['depth'] == 15.0
        assert fwd_params['cdom'] == params.fixed_cdom  # Should use fixed value
        assert fwd_params['num_bands'] == 4

    def test_get_forward_model_params_no_wavelengths(self):
        """Test that missing wavelengths raises error."""
        params = InversionParameters()
        with pytest.raises(ValueError, match="Wavelengths must be specified"):
            params.get_forward_model_params([])

    def test_set_nedr(self):
        """Test setting NEDR values."""
        params = InversionParameters(wavelengths=[443, 490, 560, 665])
        nedr_values = [0.001, 0.002, 0.001, 0.0005]

        result = params.set_nedr(nedr_values)

        assert result is params  # Method chaining
        assert np.array_equal(params.nedr, nedr_values)

    def test_set_nedr_wrong_length(self):
        """Test setting NEDR with wrong length raises error."""
        params = InversionParameters(wavelengths=[443, 490, 560, 665])
        nedr_values = [0.001, 0.002]  # Wrong length

        with pytest.raises(ValueError, match="NEDR values length"):
            params.set_nedr(nedr_values)

    def test_get_adaptive_initial_values(self):
        """Test adaptive initial value calculation."""
        params = InversionParameters(
            chl=(0.1, 10.0),
            depth=(0.5, 30.0)
        )

        # Test with observed reflectance
        observed_rrs = np.array([0.05, 0.08, 0.06, 0.03])
        initial = params.get_adaptive_initial_values(observed_rrs)

        assert len(initial) == 2  # chl and depth
        assert 0.1 <= initial[0] <= 10.0  # chl within bounds
        assert 0.5 <= initial[1] <= 30.0  # depth within bounds

    def test_get_adaptive_initial_values_no_observed(self):
        """Test adaptive initial values without observed data."""
        params = InversionParameters(
            chl=(0.1, 10.0),
            depth=(0.5, 30.0)
        )

        initial = params.get_adaptive_initial_values()

        assert len(initial) == 2
        assert all(isinstance(val, float) for val in initial)


class TestLookUpTable:
    """Test lookup table functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.params = InversionParameters(
            chl=(0.1, 10.0),
            depth=(0.5, 30.0),
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )

        self.lut = LookUpTable(self.params)

    def test_initialization(self):
        """Test LookUpTable initialization."""
        assert self.lut.inversion_parameters is self.params
        assert self.lut.param_names == ['chl', 'depth']
        assert len(self.lut.bounds) == 2
        assert self.lut.table_built is False

    @patch('sambuca.core.inversion.lut.forward_model')
    def test_build_table_basic(self, mock_forward_model):
        """Test basic lookup table building."""
        # Mock forward model results
        mock_result = Mock()
        mock_result.rrs = np.array([0.05, 0.08, 0.06, 0.03])
        mock_forward_model.return_value = mock_result

        # Build small table for testing
        self.lut.build_table(grid_size=3, progress_bar=False, use_kdtree=False)

        assert self.lut.table_built is True
        assert self.lut.param_array is not None
        assert self.lut.spectra_array is not None
        assert self.lut.param_array.shape == (9, 2)  # 3^2 combinations
        assert self.lut.spectra_array.shape == (9, 4)  # 9 combinations, 4 wavelengths

    @patch('sambuca.core.inversion.lut.forward_model')
    def test_build_table_different_grid_sizes(self, mock_forward_model):
        """Test building table with different grid sizes per parameter."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.05, 0.08, 0.06, 0.03])
        mock_forward_model.return_value = mock_result

        # Different grid sizes for each parameter
        grid_sizes = [2, 4]  # 2 for chl, 4 for depth
        self.lut.build_table(grid_size=grid_sizes, progress_bar=False, use_kdtree=False)

        assert self.lut.param_array.shape == (8, 2)  # 2*4 combinations
        assert self.lut.grid_shape == (2, 4)

    def test_build_table_no_parameters(self):
        """Test building table with no parameters raises error."""
        empty_params = InversionParameters(wavelengths=[443, 490, 560, 665])
        lut = LookUpTable(empty_params)

        with pytest.raises(ValueError, match="No parameters specified"):
            lut.build_table()

    @patch('sambuca.core.inversion.lut.forward_model')
    def test_invert_basic(self, mock_forward_model):
        """Test basic inversion functionality."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.05, 0.08, 0.06, 0.03])
        mock_forward_model.return_value = mock_result

        # Build small table
        self.lut.build_table(grid_size=2, progress_bar=False, use_kdtree=False)

        # Test inversion
        observed_rrs = np.array([0.05, 0.08, 0.06, 0.03])
        result = self.lut.invert(observed_rrs, refine=False)

        assert 'parameters' in result
        assert 'error' in result
        assert 'modeled_spectra' in result
        assert len(result['parameters']) == 2  # chl, depth

    def test_invert_not_built(self):
        """Test inversion when table not built raises error."""
        observed_rrs = np.array([0.05, 0.08, 0.06, 0.03])

        with pytest.raises(ValueError, match="Look-up table not built"):
            self.lut.invert(observed_rrs)


class TestObjectiveFunctions:
    """Test objective function implementations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.observed_rrs = np.array([0.05, 0.08, 0.06, 0.03])
        self.params = InversionParameters(
            chl=(0.1, 10.0),
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_spectral_rmse_basic(self, mock_forward_model):
        """Test basic RMSE calculation."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        # Test RMSE calculation using class-based API
        rmse_func = SpectralRMSE()
        x = [2.0]  # chl value
        error = rmse_func(x, self.observed_rrs, self.params)

        assert isinstance(error, (float, np.floating))
        assert error >= 0
        mock_forward_model.assert_called_once()

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_spectral_rmse_with_weights(self, mock_forward_model):
        """Test RMSE calculation with error weights."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        x = [2.0]
        weights = np.array([1.0, 2.0, 1.5, 0.5])

        rmse_func = SpectralRMSE(error_weight=weights)
        error = rmse_func(x, self.observed_rrs, self.params)

        assert isinstance(error, (float, np.floating))
        assert error >= 0

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_spectral_rmse_return_modeled_spectra(self, mock_forward_model):
        """Test RMSE calculation returning modeled spectra."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        x = [2.0]
        rmse_func = SpectralRMSE()
        result = rmse_func(x, self.observed_rrs, self.params, return_modeled_spectra=True)

        assert isinstance(result, dict)
        assert 'error' in result
        assert 'modeled_spectra' in result
        assert 'forward_model_results' in result

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_spectral_angle_mapper(self, mock_forward_model):
        """Test Spectral Angle Mapper calculation."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        x = [2.0]
        sam_func = SpectralAngleMapper()
        angle = sam_func(x, self.observed_rrs, self.params)

        assert isinstance(angle, (float, np.floating))
        assert 0 <= angle <= np.pi

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_spectral_angle_mapper_identical_spectra(self, mock_forward_model):
        """Test SAM with identical spectra should give zero angle."""
        mock_result = Mock()
        mock_result.rrs = self.observed_rrs.copy()
        mock_forward_model.return_value = mock_result

        x = [2.0]
        sam_func = SpectralAngleMapper()
        angle = sam_func(x, self.observed_rrs, self.params)

        assert np.isclose(angle, 0.0, atol=1e-10)

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_spectral_relative_rmse(self, mock_forward_model):
        """Test relative RMSE calculation."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        x = [2.0]
        rel_rmse_func = SpectralRelativeRMSE()
        error = rel_rmse_func(x, self.observed_rrs, self.params)

        assert isinstance(error, (float, np.floating))
        assert error >= 0

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_spectral_chi_square(self, mock_forward_model):
        """Test chi-square calculation."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        x = [2.0]
        chi_square_func = SpectralChiSquare()
        chi_square = chi_square_func(x, self.observed_rrs, self.params)

        assert isinstance(chi_square, (float, np.floating))
        assert chi_square >= 0

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_spectral_rmse_with_nedr(self, mock_forward_model):
        """Test RMSE calculation with NEDR weighting."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        x = [2.0]
        nedr = np.array([0.002, 0.003, 0.002, 0.001])

        rmse_nedr_func = SpectralRMSEWithNEDR(nedr=nedr)
        error = rmse_nedr_func(x, self.observed_rrs, self.params)

        assert isinstance(error, (float, np.floating))
        assert error >= 0

    def test_convenience_factory_functions(self):
        """Test convenience factory functions."""
        # Test that factory functions create the right instances
        rmse = create_rmse()
        assert isinstance(rmse, SpectralRMSE)
        
        sam = create_angle_mapper()
        assert isinstance(sam, SpectralAngleMapper)
        
        rel_rmse = create_relative_rmse()
        assert isinstance(rel_rmse, SpectralRelativeRMSE)
        
        chi_square = create_chi_square()
        assert isinstance(chi_square, SpectralChiSquare)
        
        rmse_nedr = create_rmse_with_nedr()
        assert isinstance(rmse_nedr, SpectralRMSEWithNEDR)


class TestOptimizationResult:
    """Test OptimizationResult dataclass."""

    def test_optimization_result_creation(self):
        """Test OptimizationResult creation and attributes."""
        # Mock forward model results
        mock_forward_results = Mock()
        mock_forward_results.rrs = np.array([0.05, 0.08, 0.06, 0.03])

        parameters = {'chl': 2.0, 'depth': 10.0}
        objective_value = 0.005
        observed_spectra = np.array([0.05, 0.08, 0.06, 0.03])
        modeled_spectra = np.array([0.04, 0.09, 0.065, 0.025])
        wavelengths = np.array([443, 490, 560, 665])

        result = OptimizationResult(
            parameters=parameters,
            objective_value=objective_value,
            observed_spectra=observed_spectra,
            modeled_spectra=modeled_spectra,
            wavelengths=wavelengths,
            convergence_status=True,
            additional_info={'iterations': 15},
            forward_model_results=mock_forward_results
        )

        assert result.parameters == parameters
        assert result.objective_value == objective_value
        assert np.array_equal(result.observed_spectra, observed_spectra)
        assert np.array_equal(result.modeled_spectra, modeled_spectra)
        assert np.array_equal(result.wavelengths, wavelengths)
        assert result.convergence_status is True
        assert result.additional_info['iterations'] == 15
        assert result.forward_model_results is mock_forward_results


class TestOptimization:
    """Test optimization functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.observed_rrs = np.array([0.05, 0.08, 0.06, 0.03])
        self.params = InversionParameters(
            chl=(0.1, 10.0),
            depth=(0.5, 30.0),
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )

    @patch('sambuca.core.inversion.optimization.forward_model')
    @patch('sambuca.core.inversion.optimization.optimize.minimize')
    def test_invert_spectrum_basic(self, mock_minimize, mock_forward_model):
        """Test basic spectrum inversion."""
        # Mock forward model
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        # Mock optimization result
        mock_opt_result = Mock()
        mock_opt_result.x = [2.0, 10.0]
        mock_opt_result.fun = 0.005
        mock_opt_result.success = True
        mock_opt_result.nit = 15
        mock_opt_result.message = "Optimization terminated successfully"
        mock_minimize.return_value = mock_opt_result

        result = invert_spectrum(self.observed_rrs, self.params)

        assert isinstance(result, OptimizationResult)
        assert result.parameters['chl'] == 2.0
        assert result.parameters['depth'] == 10.0
        assert result.objective_value == 0.005
        assert result.convergence_status is True

    def test_invert_spectrum_no_parameters(self):
        """Test inversion with no parameters raises error."""
        empty_params = InversionParameters(wavelengths=[443, 490, 560, 665])

        with pytest.raises(ValueError, match="No parameters specified"):
            invert_spectrum(self.observed_rrs, empty_params)

    @patch('sambuca.core.inversion.optimization.invert_spectrum')
    def test_multi_start_inversion(self, mock_invert):
        """Test multi-start inversion."""
        # Mock invert_spectrum to return different results
        mock_results = []
        for i in range(3):
            mock_result = Mock(spec=OptimizationResult)
            mock_result.objective_value = 0.01 + i * 0.001  # Different errors
            mock_result.parameters = {'chl': 2.0 + i, 'depth': 10.0 + i}
            mock_results.append(mock_result)

        mock_invert.side_effect = mock_results

        result = multi_start_inversion(self.observed_rrs, self.params, n_starts=3)

        # Should return the result with lowest error (first one)
        assert result is mock_results[0]
        assert mock_invert.call_count == 3


class TestPixelProcessor:
    """Test pixel processing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.params = InversionParameters(
            chl=(0.1, 10.0),
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )

    def test_process_pixel_invalid(self):
        """Test processing invalid pixel."""
        # Pixel with NaN values
        invalid_pixel = np.array([np.nan, 0.08, 0.06, 0.03])

        result = process_pixel(invalid_pixel, self.params, lut=None, refinement=False)

        assert result['status'] == 'invalid_pixel'
        assert np.isnan(result['error'])
        assert all(np.isnan(result['parameters'][p]) for p in result['parameters'])

    def test_process_pixel_negative_values(self):
        """Test processing pixel with negative values."""
        # Pixel with negative values
        invalid_pixel = np.array([-0.01, 0.08, 0.06, 0.03])

        result = process_pixel(invalid_pixel, self.params, lut=None, refinement=False)

        assert result['status'] == 'invalid_pixel'

    @patch('sambuca.core.inversion.pixel_processor.invert_spectrum')
    def test_process_pixel_valid_optimization(self, mock_invert):
        """Test processing valid pixel with optimization."""
        # Mock optimization result
        mock_result = Mock(spec=OptimizationResult)
        mock_result.parameters = {'chl': 2.0}
        mock_result.objective_value = 0.005
        mock_result.modeled_spectra = np.array([0.04, 0.09, 0.065, 0.025])
        mock_result.convergence_status = True
        mock_invert.return_value = mock_result

        valid_pixel = np.array([0.05, 0.08, 0.06, 0.03])

        result = process_pixel(valid_pixel, self.params, lut=None, refinement=False)

        assert result['status'] == 'optimization_success'
        assert result['parameters']['chl'] == 2.0
        assert result['error'] == 0.005
        assert result['convergence'] is True

    @patch('sambuca.core.inversion.pixel_processor.invert_spectrum')
    def test_process_pixel_optimization_failure(self, mock_invert):
        """Test processing pixel when optimization fails."""
        # Mock optimization to raise exception
        mock_invert.side_effect = Exception("Optimization failed")

        valid_pixel = np.array([0.05, 0.08, 0.06, 0.03])

        result = process_pixel(valid_pixel, self.params, lut=None, refinement=False)

        assert result['status'] == 'optimization_failed'
        assert 'error_message' in result
        assert np.isnan(result['error'])

    def test_process_image_invalid_dimensions(self):
        """Test processing image with invalid dimensions."""
        # Wrong number of dimensions
        invalid_image = np.random.rand(50, 50)  # Only 2D

        with pytest.raises(ValueError, match="Image must have 3 dimensions"):
            process_image(invalid_image, self.params)

    def test_process_image_band_mismatch(self):
        """Test processing image with mismatched band dimensions."""
        # Image with wrong number of bands
        invalid_image = np.random.rand(50, 50, 6)  # 6 bands, but params has 4

        with pytest.raises(ValueError, match="does not match wavelengths length"):
            process_image(invalid_image, self.params)

    @patch('sambuca.core.inversion.pixel_processor.process_pixel')
    def test_process_image_bands_first(self, mock_process_pixel):
        """Test processing image with bands-first format."""
        # Mock process_pixel to return valid result
        mock_process_pixel.return_value = {
            'parameters': {'chl': 2.0},
            'error': 0.005,
            'modeled_spectra': np.array([0.04, 0.09, 0.065, 0.025]),
            'convergence': True,
            'status': 'success'
        }

        # Create image with bands-first format
        image = np.random.rand(4, 10, 10)  # (bands, height, width)

        result = process_image(
            image,
            self.params,
            n_processes=1,
            progress_bar=False,
            use_threads=True
        )

        assert 'chl' in result
        assert result['chl'].shape == (10, 10)
        assert 'error' in result
        assert 'convergence' in result

    @patch('sambuca.core.inversion.pixel_processor.process_pixel')
    def test_process_image_bands_last(self, mock_process_pixel):
        """Test processing image with bands-last format."""
        # Mock process_pixel to return valid result
        mock_process_pixel.return_value = {
            'parameters': {'chl': 2.0},
            'error': 0.005,
            'modeled_spectra': np.array([0.04, 0.09, 0.065, 0.025]),
            'convergence': True,
            'status': 'success'
        }

        # Create image with bands-last format
        image = np.random.rand(10, 10, 4)  # (height, width, bands)

        result = process_image(
            image,
            self.params,
            n_processes=1,
            progress_bar=False,
            use_threads=True
        )

        assert 'chl' in result
        assert result['chl'].shape == (10, 10)

    @patch('sambuca.core.inversion.pixel_processor.process_pixel')
    def test_process_image_with_mask(self, mock_process_pixel):
        """Test processing image with mask."""
        # Mock process_pixel to return valid result
        mock_process_pixel.return_value = {
            'parameters': {'chl': 2.0},
            'error': 0.005,
            'modeled_spectra': np.array([0.04, 0.09, 0.065, 0.025]),
            'convergence': True,
            'status': 'success'
        }

        image = np.random.rand(5, 5, 4)
        mask = np.ones((5, 5), dtype=bool)
        mask[0:2, 0:2] = False  # Mask out some pixels

        result = process_image(
            image,
            self.params,
            mask=mask,
            n_processes=1,
            progress_bar=False,
            use_threads=True
        )

        assert 'chl' in result
        # Should have NaN values where mask is False
        assert np.isnan(result['chl'][0, 0])
        assert np.isnan(result['chl'][1, 1])

    def test_process_image_empty_mask(self):
        """Test processing image with empty mask."""
        image = np.random.rand(5, 5, 4)
        mask = np.zeros((5, 5), dtype=bool)  # All False

        with pytest.raises(ValueError, match="No pixels to process"):
            process_image(
                image,
                self.params,
                mask=mask,
                n_processes=1,
                progress_bar=False
            )

    def test_process_image_mask_shape_mismatch(self):
        """Test processing image with incorrectly shaped mask."""
        image = np.random.rand(5, 5, 4)
        mask = np.ones((3, 3), dtype=bool)  # Wrong shape

        with pytest.raises(ValueError, match="Mask shape .* does not match image shape"):
            process_image(
                image,
                self.params,
                mask=mask,
                n_processes=1,
                progress_bar=False
            )


class TestInversionIntegration:
    """Integration tests for inversion modules."""

    def setup_method(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up integration test environment."""
        shutil.rmtree(self.temp_dir)

    def test_parameter_workflow_integration(self):
        """Test complete parameter setup and usage workflow."""
        # Create parameters with realistic values
        params = InversionParameters(
            chl=(0.1, 10.0),
            depth=(0.5, 30.0),
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )

        # Test parameter bounds and names
        bounds = params.get_parameter_bounds()
        names = params.get_inversion_parameter_names()

        assert len(bounds) == 2
        assert len(names) == 2
        assert names == ['chl', 'depth']

        # Test forward model parameter generation
        x = [2.0, 10.0]  # chl=2.0, depth=10.0
        fwd_params = params.get_forward_model_params(x)

        assert fwd_params['chl'] == 2.0
        assert fwd_params['depth'] == 10.0
        assert fwd_params['cdom'] == params.fixed_cdom
        assert len(fwd_params['wavelengths']) == 4

    def test_objective_function_consistency(self):
        """Test that different objective functions give consistent results."""
        params = InversionParameters(
            chl=(0.1, 10.0),
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )

        observed_rrs = np.array([0.05, 0.08, 0.06, 0.03])
        x = [2.0]  # chl value

        # Test different objective functions using class-based API
        rmse_func = SpectralRMSE()
        sam_func = SpectralAngleMapper()

        with patch('sambuca.core.inversion.objective_functions.base.forward_model') as mock_fm_rmse:
            with patch('sambuca.core.inversion.objective_functions.base.forward_model') as mock_fm_sam:
                # Mock forward model to return consistent results
                mock_result = Mock()
                mock_result.rrs = np.array([0.05, 0.08, 0.06, 0.03])  # Perfect match
                mock_fm_rmse.return_value = mock_result
                mock_fm_sam.return_value = mock_result

                # Test different objective functions
                rmse = rmse_func(x, observed_rrs, params)
                sam = sam_func(x, observed_rrs, params)

                # Perfect match should give very small errors
                assert rmse < 1e-10
                assert sam < 1e-10  # Should be very small angle

    def test_error_metric_behavior(self):
        """Test behavior of different error metrics with known data."""
        params = InversionParameters(
            chl=(0.1, 10.0),
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )

        observed = np.array([0.05, 0.08, 0.06, 0.03])
        x = [2.0]

        # Create objective function instances
        rmse_func = SpectralRMSE()
        sam_func = SpectralAngleMapper()
        rel_rmse_func = SpectralRelativeRMSE()

        # Test with different modeled spectra
        test_cases = [
            ([0.05, 0.08, 0.06, 0.03], "identical"),  # Perfect match
            ([0.10, 0.16, 0.12, 0.06], "scaled"),  # 2x scaling
            ([0.03, 0.06, 0.04, 0.01], "reduced"),  # 0.6x scaling
        ]

        for modeled_values, case_name in test_cases:
            # Use fresh mocks for each test case to avoid state persistence
            with patch('sambuca.core.inversion.objective_functions.base.forward_model') as mock_fm:
                mock_result = Mock()
                mock_result.rrs = np.array(modeled_values)
                mock_fm.return_value = mock_result

                rmse = rmse_func(x, observed, params)
                sam = sam_func(x, observed, params)
                rel_rmse = rel_rmse_func(x, observed, params)

                if case_name == "identical":
                    # Perfect match should give zero errors
                    assert rmse < 1e-10, f"RMSE for {case_name}: expected < 1e-10, got {rmse}"
                    assert sam < 1e-10, f"SAM for {case_name}: expected < 1e-10, got {sam}"
                    assert rel_rmse < 1e-10, f"Rel RMSE for {case_name}: expected < 1e-10, got {rel_rmse}"
                elif case_name in ["scaled", "reduced"]:
                    # Scaled versions should have:
                    # - Non-zero RMSE and relative RMSE
                    # - Very small SAM (same spectral shape)
                    assert rmse > 0, f"RMSE for {case_name}: expected > 0, got {rmse}"
                    assert rel_rmse > 0, f"Rel RMSE for {case_name}: expected > 0, got {rel_rmse}"
                    assert sam < 0.2, f"SAM for {case_name}: expected < 0.2, got {sam}"  # Small angle for same shape
