import pytest

from sambuca_core import SambucaException, DataValidationError


class TestExceptions:
    """Test custom exceptions."""

    def test_sambuca_exception(self):
        """Test SambucaException."""
        with pytest.raises(SambucaException):
            raise SambucaException("Test exception")

    def test_data_validation_error(self):
        """Test DataValidationError."""
        with pytest.raises(DataValidationError):
            raise DataValidationError("Test validation error")

    def test_exception_inheritance(self):
        """Test exception inheritance."""
        # DataValidationError should inherit from SambucaException
        assert issubclass(DataValidationError, SambucaException)