import sambuca.core as sbc

class TestUtilities:
    """Test utility functions."""

    def test_strictly_increasing(self):
        """Test strictly_increasing function."""
        assert sbc.strictly_increasing([1, 2, 3, 4])
        assert not sbc.strictly_increasing([1, 2, 2, 3])
        assert not sbc.strictly_increasing([4, 3, 2, 1])
        assert sbc.strictly_increasing([])  # Empty sequence

    def test_strictly_decreasing(self):
        """Test strictly_decreasing function."""
        assert sbc.strictly_decreasing([4, 3, 2, 1])
        assert not sbc.strictly_decreasing([4, 3, 3, 1])
        assert not sbc.strictly_decreasing([1, 2, 3, 4])
        assert sbc.strictly_decreasing([])  # Empty sequence
