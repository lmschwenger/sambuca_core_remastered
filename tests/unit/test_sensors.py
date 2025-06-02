import pytest

from sambuca.core.sensors import SensorFactory, Sentinel2Sensor


class TestSensors:
    """Test sensor configurations."""

    def test_sensor_factory(self):
        """Test sensor factory."""
        sensor = SensorFactory.create('sentinel2')
        assert isinstance(sensor, Sentinel2Sensor)
        assert sensor.name == "Sentinel-2"

        # Test available sensors
        available = SensorFactory.list_available()
        assert 'sentinel2' in available
        assert 's2' in available  # Alias

    def test_sentinel2_sensor(self):
        """Test Sentinel-2 sensor configuration."""
        sensor = Sentinel2Sensor()

        # Test basic properties
        assert sensor.name == "Sentinel-2"
        assert isinstance(sensor.band_wavelengths, dict)
        assert 'B2' in sensor.band_wavelengths
        assert 'B3' in sensor.band_wavelengths
        assert 'B4' in sensor.band_wavelengths

        # Test standard configurations
        bands, wavelengths = sensor.get_standard_config('bathymetry')
        assert len(bands) == len(wavelengths)
        assert 'B2' in bands
        assert 'B3' in bands
        assert 'B4' in bands

    def test_unknown_sensor(self):
        """Test handling of unknown sensors."""
        with pytest.raises(ValueError):
            SensorFactory.create('unknown_sensor')