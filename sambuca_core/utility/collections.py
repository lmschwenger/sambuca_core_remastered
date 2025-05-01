"""Collection utility functions."""

from typing import Dict, Any, TypeVar, Iterator, Iterable, Tuple

T = TypeVar('T')


def merge_dictionary(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    """Merges the source dictionary into the target dictionary.

    Args:
        target: The target dictionary.
        source: The source dictionary.

    Returns:
        The modified target dictionary.
    """
    for key, value in source.items():
        if key not in target:
            target[key] = value

    return target


def pairwise(iterable: Iterable[T]) -> Iterator[Tuple[T, T]]:
    """Returns an iterator of paired items, overlapping, from the original.

    Args:
        iterable: The input iterable.

    Returns:
        An iterator over pairs of successive items.

    Example:
        >>> list(pairwise([1, 2, 3, 4]))
        [(1, 2), (2, 3), (3, 4)]
    """
    iterator = iter(iterable)
    try:
        a = next(iterator)
    except StopIteration:
        return

    for b in iterator:
        yield a, b
        a = b