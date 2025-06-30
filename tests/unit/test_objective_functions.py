"""Unit tests for sambuca.core.inversion.objective_functions module."""

from unittest.mock import Mock, patch
import numpy as np
import pytest

from sambuca.core.inversion.objective_functions import (
    ObjectiveFunction,
    ForwardModelObjectiveFunction,
    SpectralRMSE,
    SpectralAngleMapper,
    SpectralRelativeRMSE,
    SpectralChiSquare,
    SpectralRMSEWithNEDR,
    create_rmse,
    create_rmse_with_nedr,
    create_angle_mapper,
    create_relative_rmse,
    create_chi_square
)
from sambuca.core.inversion.parameters import InversionParameters


class TestBaseObjectiveFunction:
    """Test the base ObjectiveFunction abstract class."""

    def test_cannot_instantiate_abstract_base(self):
        """Test that ObjectiveFunction cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ObjectiveFunction()

    def test_validate_inputs_parameter_length_mismatch(self):
        """Test validation fails when parameter length doesn't match bounds."""
        # Create a concrete implementation for testing
        class TestObjectiveFunction(ForwardModelObjectiveFunction):
            @property
            def name(self):
                return "test"
            
            @property
            def description(self):
                return "test function"
                
            def __call__(self, params, observed_rrs, inversion_parameters, **kwargs):
                return 0.0

        obj_func = TestObjectiveFunction()
        
        params = InversionParameters(
            chl=(0.1, 10.0),
            depth=(0.5, 30.0),
            wavelengths=[443, 490, 560, 665]
        )
        
        observed_rrs = np.array([0.05, 0.08, 0.06, 0.03])
        invalid_params = [1.0]  # Should be 2 parameters (chl, depth)
        
        with pytest.raises(ValueError, match="params length.*must match number of parameters"):
            obj_func.validate_inputs(invalid_params, observed_rrs, params)

    def test_validate_inputs_wavelength_length_mismatch(self):
        """Test validation fails when observed_rrs length doesn't match wavelengths."""
        class TestObjectiveFunction(ForwardModelObjectiveFunction):
            @property
            def name(self):
                return "test"
            
            @property
            def description(self):
                return "test function"
                
            def __call__(self, params, observed_rrs, inversion_parameters, **kwargs):
                return 0.0

        obj_func = TestObjectiveFunction()
        
        params = InversionParameters(
            chl=(0.1, 10.0),
            wavelengths=[443, 490, 560, 665]
        )
        
        invalid_observed_rrs = np.array([0.05, 0.08])  # Only 2 values, should be 4
        valid_params = [1.0]
        
        with pytest.raises(ValueError, match="observed_rrs length.*must match wavelengths length"):
            obj_func.validate_inputs(valid_params, invalid_observed_rrs, params)

    def test_validate_inputs_invalid_observed_rrs(self):
        """Test validation fails with NaN or negative observed_rrs."""
        class TestObjectiveFunction(ForwardModelObjectiveFunction):
            @property
            def name(self):
                return "test"
            
            @property
            def description(self):
                return "test function"
                
            def __call__(self, params, observed_rrs, inversion_parameters, **kwargs):
                return 0.0

        obj_func = TestObjectiveFunction()
        
        params = InversionParameters(
            chl=(0.1, 10.0),
            wavelengths=[443, 490, 560, 665]
        )
        
        # Test with NaN values
        nan_observed_rrs = np.array([0.05, np.nan, 0.06, 0.03])
        valid_params = [1.0]
        
        with pytest.raises(ValueError, match="observed_rrs contains invalid values"):
            obj_func.validate_inputs(valid_params, nan_observed_rrs, params)
        
        # Test with negative values
        negative_observed_rrs = np.array([0.05, -0.01, 0.06, 0.03])
        
        with pytest.raises(ValueError, match="observed_rrs contains invalid values"):
            obj_func.validate_inputs(valid_params, negative_observed_rrs, params)


class TestForwardModelObjectiveFunction:
    """Test the ForwardModelObjectiveFunction base class."""

    def setup_method(self):
        """Set up test fixtures."""
        class TestForwardModelObjectiveFunction(ForwardModelObjectiveFunction):
            @property
            def name(self):
                return "test_forward_model"
            
            @property
            def description(self):
                return "test forward model function"
                
            def __call__(self, params, observed_rrs, inversion_parameters, **kwargs):
                return 0.0

        self.obj_func = TestForwardModelObjectiveFunction()
        self.params = InversionParameters(
            chl=(0.1, 10.0),
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_run_forward_model(self, mock_forward_model):
        """Test running the forward model."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        x = [2.0]  # chl value
        result = self.obj_func.run_forward_model(x, self.params)

        assert result is mock_result
        mock_forward_model.assert_called_once()
        # Verify forward model was called with the right parameters
        call_args = mock_forward_model.call_args[1]
        assert call_args['chl'] == 2.0

    def test_create_detailed_result(self):
        """Test creating detailed result dictionary."""
        error = 0.005
        modeled_rrs = np.array([0.04, 0.09, 0.065, 0.025])
        forward_results = Mock()
        
        result = self.obj_func.create_detailed_result(
            error=error,
            modeled_rrs=modeled_rrs,
            forward_results=forward_results,
            additional_param="test_value"
        )

        assert result['error'] == error
        assert np.array_equal(result['modeled_spectra'], modeled_rrs)
        assert result['forward_model_results'] is forward_results
        assert result['objective_function'] == "test_forward_model"
        assert result['additional_param'] == "test_value"


class TestSpectralRMSE:
    """Test SpectralRMSE objective function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.params = InversionParameters(
            chl=(0.1, 10.0),
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )
        self.observed_rrs = np.array([0.05, 0.08, 0.06, 0.03])

    def test_initialization_default(self):
        """Test SpectralRMSE initialization with defaults."""
        rmse = SpectralRMSE()
        
        assert rmse.name == "spectral_rmse"
        assert "Root Mean Square Error" in rmse.description
        assert rmse.error_weight is None

    def test_initialization_with_weights(self):
        """Test SpectralRMSE initialization with weights."""
        weights = np.array([1.0, 2.0, 1.5, 0.5])
        rmse = SpectralRMSE(error_weight=weights)
        
        assert np.array_equal(rmse.error_weight, weights)

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_basic(self, mock_forward_model):
        """Test basic RMSE calculation."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        rmse = SpectralRMSE()
        x = [2.0]  # chl value
        
        error = rmse(x, self.observed_rrs, self.params)

        assert isinstance(error, (float, np.floating))
        assert error >= 0
        # Calculate expected RMSE manually
        expected = np.sqrt(np.mean((mock_result.rrs - self.observed_rrs) ** 2))
        assert np.isclose(error, expected)

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_with_weights(self, mock_forward_model):
        """Test RMSE calculation with error weights."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        weights = np.array([1.0, 2.0, 1.5, 0.5])
        rmse = SpectralRMSE(error_weight=weights)
        x = [2.0]

        error = rmse(x, self.observed_rrs, self.params)

        assert isinstance(error, (float, np.floating))
        assert error >= 0
        # Should be different from unweighted version
        
        # Test with weights provided in call (should override instance weights)
        override_weights = np.array([0.5, 1.0, 0.8, 2.0])
        error_override = rmse(x, self.observed_rrs, self.params, error_weight=override_weights)
        assert error_override != error  # Should be different

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_return_detailed_results(self, mock_forward_model):
        """Test RMSE calculation returning detailed results."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        rmse = SpectralRMSE()
        x = [2.0]

        result = rmse(x, self.observed_rrs, self.params, return_modeled_spectra=True)

        assert isinstance(result, dict)
        assert 'error' in result
        assert 'modeled_spectra' in result
        assert 'forward_model_results' in result
        assert 'objective_function' in result
        assert 'weights_used' in result
        assert np.array_equal(result['modeled_spectra'], mock_result.rrs)
        assert result['objective_function'] == "spectral_rmse"

    def test_call_validation_error(self):
        """Test that validation errors are raised."""
        rmse = SpectralRMSE()
        invalid_params = [1.0, 2.0]  # Too many parameters
        
        with pytest.raises(ValueError):
            rmse(invalid_params, self.observed_rrs, self.params)


class TestSpectralAngleMapper:
    """Test SpectralAngleMapper objective function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.params = InversionParameters(
            chl=(0.1, 10.0),
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )
        self.observed_rrs = np.array([0.05, 0.08, 0.06, 0.03])

    def test_initialization(self):
        """Test SpectralAngleMapper initialization."""
        sam = SpectralAngleMapper()
        
        assert sam.name == "spectral_angle_mapper"
        assert "spectral angle" in sam.description.lower()

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_basic(self, mock_forward_model):
        """Test basic SAM calculation."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        sam = SpectralAngleMapper()
        x = [2.0]

        angle = sam(x, self.observed_rrs, self.params)

        assert isinstance(angle, (float, np.floating))
        assert 0 <= angle <= np.pi

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_identical_spectra(self, mock_forward_model):
        """Test SAM with identical spectra should give zero angle."""
        mock_result = Mock()
        mock_result.rrs = self.observed_rrs.copy()
        mock_forward_model.return_value = mock_result

        sam = SpectralAngleMapper()
        x = [2.0]

        angle = sam(x, self.observed_rrs, self.params)

        assert np.isclose(angle, 0.0, atol=1e-10)

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_opposite_spectra(self, mock_forward_model):
        """Test SAM with opposite spectra should give maximum angle."""
        mock_result = Mock()
        mock_result.rrs = -self.observed_rrs  # Opposite direction
        mock_forward_model.return_value = mock_result

        sam = SpectralAngleMapper()
        x = [2.0]

        angle = sam(x, self.observed_rrs, self.params)

        assert np.isclose(angle, np.pi, atol=1e-6)

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_zero_norm_case(self, mock_forward_model):
        """Test SAM with zero norm case."""
        mock_result = Mock()
        mock_result.rrs = np.zeros_like(self.observed_rrs)
        mock_forward_model.return_value = mock_result

        sam = SpectralAngleMapper()
        x = [2.0]

        angle = sam(x, self.observed_rrs, self.params)

        # Should return π/2 (90 degrees) when one spectrum is zero
        assert np.isclose(angle, np.pi / 2, atol=1e-6)

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_return_detailed_results(self, mock_forward_model):
        """Test SAM returning detailed results."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        sam = SpectralAngleMapper()
        x = [2.0]

        result = sam(x, self.observed_rrs, self.params, return_modeled_spectra=True)

        assert isinstance(result, dict)
        assert 'error' in result
        assert 'modeled_spectra' in result
        assert 'angle_degrees' in result
        assert 'cosine_similarity' in result
        assert result['objective_function'] == "spectral_angle_mapper"
        
        # Check angle conversion
        angle_rad = result['error']
        angle_deg = result['angle_degrees']
        assert np.isclose(angle_deg, np.degrees(angle_rad))


class TestSpectralRelativeRMSE:
    """Test SpectralRelativeRMSE objective function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.params = InversionParameters(
            chl=(0.1, 10.0),
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )
        self.observed_rrs = np.array([0.05, 0.08, 0.06, 0.03])

    def test_initialization_default(self):
        """Test SpectralRelativeRMSE initialization with defaults."""
        rel_rmse = SpectralRelativeRMSE()
        
        assert rel_rmse.name == "spectral_relative_rmse"
        assert "relative" in rel_rmse.description.lower()
        assert rel_rmse.epsilon == 1e-6

    def test_initialization_custom_epsilon(self):
        """Test SpectralRelativeRMSE initialization with custom epsilon."""
        custom_epsilon = 1e-8
        rel_rmse = SpectralRelativeRMSE(epsilon=custom_epsilon)
        
        assert rel_rmse.epsilon == custom_epsilon

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_basic(self, mock_forward_model):
        """Test basic relative RMSE calculation."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        rel_rmse = SpectralRelativeRMSE()
        x = [2.0]

        error = rel_rmse(x, self.observed_rrs, self.params)

        assert isinstance(error, (float, np.floating))
        assert error >= 0
        
        # Verify relative calculation
        expected_relative_diff = (mock_result.rrs - self.observed_rrs) / (self.observed_rrs + rel_rmse.epsilon)
        expected = np.sqrt(np.mean(expected_relative_diff ** 2))
        assert np.isclose(error, expected)

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_with_epsilon_override(self, mock_forward_model):
        """Test relative RMSE with epsilon override."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        rel_rmse = SpectralRelativeRMSE(epsilon=1e-6)
        x = [2.0]
        override_epsilon = 1e-4

        error = rel_rmse(x, self.observed_rrs, self.params, epsilon=override_epsilon)

        # Should use the override epsilon
        expected_relative_diff = (mock_result.rrs - self.observed_rrs) / (self.observed_rrs + override_epsilon)
        expected = np.sqrt(np.mean(expected_relative_diff ** 2))
        assert np.isclose(error, expected)

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_return_detailed_results(self, mock_forward_model):
        """Test relative RMSE returning detailed results."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        rel_rmse = SpectralRelativeRMSE()
        x = [2.0]

        result = rel_rmse(x, self.observed_rrs, self.params, return_modeled_spectra=True)

        assert isinstance(result, dict)
        assert 'error' in result
        assert 'modeled_spectra' in result
        assert 'epsilon_used' in result
        assert result['objective_function'] == "spectral_relative_rmse"


class TestSpectralRMSEWithNEDR:
    """Test SpectralRMSEWithNEDR objective function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.params = InversionParameters(
            chl=(0.1, 10.0),
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )
        self.observed_rrs = np.array([0.05, 0.08, 0.06, 0.03])
        self.nedr_values = np.array([0.002, 0.003, 0.002, 0.001])

    def test_initialization_default(self):
        """Test SpectralRMSEWithNEDR initialization with defaults."""
        rmse_nedr = SpectralRMSEWithNEDR()
        
        assert rmse_nedr.name == "spectral_rmse_with_nedr"
        assert "nedr" in rmse_nedr.description.lower()
        assert rmse_nedr.nedr is None

    def test_initialization_with_nedr(self):
        """Test SpectralRMSEWithNEDR initialization with NEDR values."""
        rmse_nedr = SpectralRMSEWithNEDR(nedr=self.nedr_values)
        
        assert np.array_equal(rmse_nedr.nedr, self.nedr_values)

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_with_nedr(self, mock_forward_model):
        """Test NEDR-weighted RMSE calculation."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        rmse_nedr = SpectralRMSEWithNEDR(nedr=self.nedr_values)
        x = [2.0]

        error = rmse_nedr(x, self.observed_rrs, self.params)

        assert isinstance(error, (float, np.floating))
        assert error >= 0
        
        # Verify NEDR weighting calculation
        weights = 1.0 / (self.nedr_values ** 2)
        weighted_squared_diff = weights * ((mock_result.rrs - self.observed_rrs) ** 2)
        expected = np.sqrt(np.sum(weighted_squared_diff) / np.sum(weights))
        assert np.isclose(error, expected)

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_without_nedr_fallback_to_standard_rmse(self, mock_forward_model):
        """Test that without NEDR it falls back to standard RMSE."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        rmse_nedr = SpectralRMSEWithNEDR()  # No NEDR values
        x = [2.0]

        error = rmse_nedr(x, self.observed_rrs, self.params)

        # Should fall back to standard RMSE
        expected = np.sqrt(np.mean((mock_result.rrs - self.observed_rrs) ** 2))
        assert np.isclose(error, expected)

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_nedr_from_inversion_parameters(self, mock_forward_model):
        """Test using NEDR from inversion parameters."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        # Set NEDR in inversion parameters
        params_with_nedr = self.params
        params_with_nedr.nedr = self.nedr_values

        rmse_nedr = SpectralRMSEWithNEDR()  # No instance NEDR
        x = [2.0]

        error = rmse_nedr(x, self.observed_rrs, params_with_nedr)

        # Should use NEDR from inversion parameters
        weights = 1.0 / (self.nedr_values ** 2)
        weighted_squared_diff = weights * ((mock_result.rrs - self.observed_rrs) ** 2)
        expected = np.sqrt(np.sum(weighted_squared_diff) / np.sum(weights))
        assert np.isclose(error, expected)

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_nedr_override(self, mock_forward_model):
        """Test NEDR override in function call."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        instance_nedr = np.array([0.001, 0.001, 0.001, 0.001])
        override_nedr = np.array([0.005, 0.005, 0.005, 0.005])

        rmse_nedr = SpectralRMSEWithNEDR(nedr=instance_nedr)
        x = [2.0]

        error = rmse_nedr(x, self.observed_rrs, self.params, nedr=override_nedr)

        # Should use override NEDR, not instance NEDR
        weights = 1.0 / (override_nedr ** 2)
        weighted_squared_diff = weights * ((mock_result.rrs - self.observed_rrs) ** 2)
        expected = np.sqrt(np.sum(weighted_squared_diff) / np.sum(weights))
        assert np.isclose(error, expected)

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_return_detailed_results(self, mock_forward_model):
        """Test NEDR-weighted RMSE returning detailed results."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        rmse_nedr = SpectralRMSEWithNEDR(nedr=self.nedr_values)
        x = [2.0]

        result = rmse_nedr(x, self.observed_rrs, self.params, return_modeled_spectra=True)

        assert isinstance(result, dict)
        assert 'error' in result
        assert 'modeled_spectra' in result
        assert 'nedr_used' in result
        assert 'nedr_values' in result
        assert result['objective_function'] == "spectral_rmse_with_nedr"
        assert result['nedr_used'] is True
        assert np.array_equal(result['nedr_values'], self.nedr_values)


class TestSpectralChiSquare:
    """Test SpectralChiSquare objective function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.params = InversionParameters(
            chl=(0.1, 10.0),
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )
        self.observed_rrs = np.array([0.05, 0.08, 0.06, 0.03])

    def test_initialization_default(self):
        """Test SpectralChiSquare initialization with defaults."""
        chi_square = SpectralChiSquare()
        
        assert chi_square.name == "spectral_chi_square"
        assert "chi" in chi_square.description.lower()
        assert chi_square.uncertainty is None

    def test_initialization_with_uncertainty(self):
        """Test SpectralChiSquare initialization with uncertainty values."""
        uncertainty = np.array([0.002, 0.003, 0.002, 0.001])
        chi_square = SpectralChiSquare(uncertainty=uncertainty)
        
        assert np.array_equal(chi_square.uncertainty, uncertainty)

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_with_uncertainty(self, mock_forward_model):
        """Test chi-square calculation with uncertainty."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        uncertainty = np.array([0.002, 0.003, 0.002, 0.001])
        chi_square = SpectralChiSquare(uncertainty=uncertainty)
        x = [2.0]

        error = chi_square(x, self.observed_rrs, self.params)

        assert isinstance(error, (float, np.floating))
        assert error >= 0
        
        # Verify chi-square calculation
        squared_diff = ((mock_result.rrs - self.observed_rrs) / uncertainty) ** 2
        expected = np.sum(squared_diff)
        assert np.isclose(error, expected)

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_call_without_uncertainty_uses_defaults(self, mock_forward_model):
        """Test chi-square calculation without uncertainty uses default values."""
        mock_result = Mock()
        mock_result.rrs = np.array([0.04, 0.09, 0.065, 0.025])
        mock_forward_model.return_value = mock_result

        chi_square = SpectralChiSquare()  # No uncertainty values
        x = [2.0]

        error = chi_square(x, self.observed_rrs, self.params)

        assert isinstance(error, (float, np.floating))
        assert error >= 0
        # Should use default uncertainty of 0.001 for all bands
        default_uncertainty = np.full_like(self.observed_rrs, 0.001)
        squared_diff = ((mock_result.rrs - self.observed_rrs) / default_uncertainty) ** 2
        expected = np.sum(squared_diff)
        assert np.isclose(error, expected)


class TestConvenienceFactoryFunctions:
    """Test convenience factory functions."""

    def test_create_rmse_default(self):
        """Test create_rmse with default parameters."""
        rmse = create_rmse()
        
        assert isinstance(rmse, SpectralRMSE)
        assert rmse.error_weight is None

    def test_create_rmse_with_weights(self):
        """Test create_rmse with error weights."""
        weights = np.array([1.0, 2.0, 1.5, 0.5])
        rmse = create_rmse(error_weight=weights)
        
        assert isinstance(rmse, SpectralRMSE)
        assert np.array_equal(rmse.error_weight, weights)

    def test_create_rmse_with_nedr_default(self):
        """Test create_rmse_with_nedr with default parameters."""
        rmse_nedr = create_rmse_with_nedr()
        
        assert isinstance(rmse_nedr, SpectralRMSEWithNEDR)
        assert rmse_nedr.nedr is None

    def test_create_rmse_with_nedr_values(self):
        """Test create_rmse_with_nedr with NEDR values."""
        nedr = np.array([0.002, 0.003, 0.002, 0.001])
        rmse_nedr = create_rmse_with_nedr(nedr=nedr)
        
        assert isinstance(rmse_nedr, SpectralRMSEWithNEDR)
        assert np.array_equal(rmse_nedr.nedr, nedr)

    def test_create_angle_mapper(self):
        """Test create_angle_mapper."""
        sam = create_angle_mapper()
        
        assert isinstance(sam, SpectralAngleMapper)

    def test_create_relative_rmse_default(self):
        """Test create_relative_rmse with default epsilon."""
        rel_rmse = create_relative_rmse()
        
        assert isinstance(rel_rmse, SpectralRelativeRMSE)
        assert rel_rmse.epsilon == 1e-6

    def test_create_relative_rmse_custom_epsilon(self):
        """Test create_relative_rmse with custom epsilon."""
        epsilon = 1e-8
        rel_rmse = create_relative_rmse(epsilon=epsilon)
        
        assert isinstance(rel_rmse, SpectralRelativeRMSE)
        assert rel_rmse.epsilon == epsilon

    def test_create_chi_square_default(self):
        """Test create_chi_square with default parameters."""
        chi_square = create_chi_square()
        
        assert isinstance(chi_square, SpectralChiSquare)
        assert chi_square.uncertainty is None

    def test_create_chi_square_with_uncertainty(self):
        """Test create_chi_square with uncertainty values."""
        uncertainty = np.array([0.002, 0.003, 0.002, 0.001])
        chi_square = create_chi_square(uncertainty=uncertainty)
        
        assert isinstance(chi_square, SpectralChiSquare)
        assert np.array_equal(chi_square.uncertainty, uncertainty)


class TestObjectiveFunctionIntegration:
    """Integration tests for objective functions working together."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.params = InversionParameters(
            chl=(0.1, 10.0),  # Only chl as inversion parameter
            depth=None,  # Explicitly ensure depth is not inverted
            cdom=None,   # Explicitly ensure cdom is not inverted
            nap=None,    # Explicitly ensure nap is not inverted
            substrate_fraction=None,  # Explicitly ensure substrate_fraction is not inverted
            wavelengths=[443, 490, 560, 665],
            a_water=[0.01, 0.02, 0.1, 0.5],
            a_ph_star=[0.05, 0.03, 0.02, 0.01],
            substrate1=[0.1, 0.2, 0.3, 0.4]
        )
        self.observed_rrs = np.array([0.05, 0.08, 0.06, 0.03])

    @patch('sambuca.core.inversion.objective_functions.base.forward_model')
    def test_multiple_objective_functions_consistency(self, mock_forward_model):
        """Test that different objective functions work consistently."""
        # Mock forward model to return the same results for all functions
        mock_result = Mock()
        mock_result.rrs = self.observed_rrs.copy()  # Perfect match
        mock_forward_model.return_value = mock_result

        x = [2.0]  # chl value

        # Test different objective functions
        rmse = SpectralRMSE()
        sam = SpectralAngleMapper()
        rel_rmse = SpectralRelativeRMSE()

        rmse_error = rmse(x, self.observed_rrs, self.params)
        sam_error = sam(x, self.observed_rrs, self.params)
        rel_rmse_error = rel_rmse(x, self.observed_rrs, self.params)

        # Perfect match should give very small errors for all functions
        assert rmse_error < 1e-10
        assert sam_error < 1e-10
        assert rel_rmse_error < 1e-10

    def test_objective_function_error_scaling(self):
        """Test how objective functions scale with different error magnitudes."""
        # Test with different error levels
        error_levels = [
            np.array([0.05, 0.08, 0.06, 0.03]),  # Perfect match
            np.array([0.055, 0.088, 0.066, 0.033]),  # 10% error
            np.array([0.06, 0.096, 0.072, 0.036]),  # 20% error
        ]

        rmse = SpectralRMSE()
        x = [2.0]
        
        errors = []
        
        # Test each error level with a fresh mock
        for i, modeled_values in enumerate(error_levels):
            with patch('sambuca.core.inversion.objective_functions.base.forward_model') as mock_forward_model:
                mock_result = Mock()
                mock_result.rrs = modeled_values
                mock_forward_model.return_value = mock_result
                
                error = rmse(x, self.observed_rrs, self.params)
                errors.append(error)

        # Errors should increase monotonically
        assert errors[0] < errors[1] < errors[2], f"Expected increasing errors, got: {errors}"
        # First error should be very small (perfect match)
        assert errors[0] < 1e-10, f"Expected first error < 1e-10, got: {errors[0]}"

    def test_objective_function_parameter_validation_consistency(self):
        """Test that all objective functions validate parameters consistently."""
        invalid_params = [1.0, 2.0]  # Too many parameters (should be 1)
        
        objective_functions = [
            SpectralRMSE(),
            SpectralAngleMapper(),
            SpectralRelativeRMSE(),
            SpectralRMSEWithNEDR(),
            SpectralChiSquare()
        ]

        for obj_func in objective_functions:
            with pytest.raises(ValueError, match="params length.*must match"):
                obj_func(invalid_params, self.observed_rrs, self.params)
