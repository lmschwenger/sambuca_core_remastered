"""Unit tests for sambuca.core.constants module."""

from sambuca.core.constants import (
    REFRACTIVE_INDEX_FRESH_WATER,
    REFRACTIVE_INDEX_SEAWATER
)


class TestConstants:
    """Test physical constants used in Sambuca."""

    def test_refractive_index_fresh_water(self):
        """Test fresh water refractive index constant."""
        assert REFRACTIVE_INDEX_FRESH_WATER == 1.3330
        assert isinstance(REFRACTIVE_INDEX_FRESH_WATER, float)
        assert 1.3 < REFRACTIVE_INDEX_FRESH_WATER < 1.4

    def test_refractive_index_seawater(self):
        """Test seawater refractive index constant."""
        assert REFRACTIVE_INDEX_SEAWATER == 1.33784
        assert isinstance(REFRACTIVE_INDEX_SEAWATER, float)
        assert REFRACTIVE_INDEX_SEAWATER > REFRACTIVE_INDEX_FRESH_WATER
        assert 1.33 < REFRACTIVE_INDEX_SEAWATER < 1.35

    def test_refractive_index_difference(self):
        """Test the difference between fresh and sea water refractive indices."""
        difference = REFRACTIVE_INDEX_SEAWATER - REFRACTIVE_INDEX_FRESH_WATER
        assert 0.003 < difference < 0.01
        assert abs(difference - 0.00484) < 0.001

    def test_constants_precision(self):
        """Test that constants have appropriate precision."""
        fresh_str = str(REFRACTIVE_INDEX_FRESH_WATER)
        sea_str = str(REFRACTIVE_INDEX_SEAWATER)

        assert len(fresh_str.split('.')[1]) >= 3
        assert len(sea_str.split('.')[1]) >= 5
