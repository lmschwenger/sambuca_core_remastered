from sambuca.core.inversion import InversionParameters


class TestInversionParameters:
    """Test the InversionParameters class."""

    def setup_method(self):
        """Set up test data."""
        self.wavelengths = [450, 550, 650, 750]
        self.a_water = [0.01, 0.02, 0.1, 0.5]
        self.a_ph_star = [0.05, 0.03, 0.02, 0.01]
        self.substrate1 = [0.1, 0.2, 0.3, 0.4]

    def test_parameter_bounds(self):
        """Test parameter bounds functionality."""
        params = InversionParameters(
            chl=(0.1, 10.0),
            depth=(0.5, 15.0),
            wavelengths=self.wavelengths,
            a_water=self.a_water,
            a_ph_star=self.a_ph_star,
            substrate1=self.substrate1
        )

        bounds = params.get_parameter_bounds()
        param_names = params.get_inversion_parameter_names()

        assert len(bounds) == 2
        assert len(param_names) == 2
        assert 'chl' in param_names
        assert 'depth' in param_names
        assert bounds[0] == (0.1, 10.0)  # chl bounds
        assert bounds[1] == (0.5, 15.0)  # depth bounds

    def test_forward_model_params(self):
        """Test conversion to forward model parameters."""
        params = InversionParameters(
            chl=(0.1, 10.0),
            fixed_cdom=0.1,
            fixed_nap=1.0,
            fixed_depth=5.0,
            wavelengths=self.wavelengths,
            a_water=self.a_water,
            a_ph_star=self.a_ph_star,
            substrate1=self.substrate1
        )

        # Test parameter conversion
        x = [2.0]  # chl value
        forward_params = params.get_forward_model_params(x)

        assert forward_params['chl'] == 2.0
        assert forward_params['cdom'] == 0.1
        assert forward_params['nap'] == 1.0
        assert forward_params['depth'] == 5.0
        assert len(forward_params['wavelengths']) == 4

    def test_initial_values(self):
        """Test initial value generation."""
        params = InversionParameters(
            chl=(0.1, 10.0),
            depth=(0.5, 15.0),
            wavelengths=self.wavelengths
        )

        initial_values = params.get_initial_values()

        assert len(initial_values) == 2
        assert initial_values[0] == 5.05  # (0.1 + 10.0) / 2
        assert initial_values[1] == 7.75  # (0.5 + 15.0) / 2