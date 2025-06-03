"""NumPy utility functions."""

from typing import Sequence, Union, TypeVar

import numpy as np

NumericType = TypeVar('NumericType', bound=Union[int, float])


def strictly_increasing(sequence: Sequence[NumericType]) -> bool:
    """Tests if a sequence is strictly increasing.

    Args:
        sequence: The sequence to test.

    Returns:
        True if the sequence is strictly increasing.
    """
    if not sequence:
        return True
    return all(x < y for x, y in zip(sequence[:-1], sequence[1:]))


def strictly_decreasing(sequence: Sequence[NumericType]) -> bool:
    """Tests if a sequence is strictly decreasing.

    Args:
        sequence: The sequence to test.

    Returns:
        True if the sequence is strictly decreasing.
    """
    if not sequence:
        return True
    return all(x > y for x, y in zip(sequence[:-1], sequence[1:]))