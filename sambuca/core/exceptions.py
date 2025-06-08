"""Sambuca exception definitions."""


class SambucaException(Exception):
    """Root exception class for Sambuca exceptions.

    Only used as a base class for any Sambuca errors.
    This exception is never raised directly.
    """

    pass


class UnsupportedDataFormatError(SambucaException):
    """The file format is not supported by Sambuca."""

    pass


class DataValidationError(SambucaException):
    """The data file failed validation."""

    pass


class DataFetchError(SambucaException):
    """Error occurred while fetching external data."""

    pass


class MissingDependencyError(SambucaException):
    """Required optional dependency is not installed."""

    pass
