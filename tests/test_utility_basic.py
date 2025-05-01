"""Basic tests for the utility functions."""

import tempfile
import os
from pathlib import Path

import numpy as np
import pytest

import sambuca_core as sbc


def test_strictly_increasing():
    """Test the strictly_increasing function."""
    # Test strictly increasing sequence
    assert sbc.strictly_increasing([1, 2, 3, 4, 5])
    assert sbc.strictly_increasing([0.1, 0.2, 0.3, 0.4])
    assert sbc.strictly_increasing([-5, -3, -1, 0, 1])

    # Test non-strictly increasing sequences
    assert not sbc.strictly_increasing([1, 2, 2, 3, 4])
    assert not sbc.strictly_increasing([1, 2, 3, 2, 5])
    assert not sbc.strictly_increasing([5, 4, 3, 2, 1])

    # Test empty and single element
    assert sbc.strictly_increasing([])
    assert sbc.strictly_increasing([1])


def test_strictly_decreasing():
    """Test the strictly_decreasing function."""
    # Test strictly decreasing sequence
    assert sbc.strictly_decreasing([5, 4, 3, 2, 1])
    assert sbc.strictly_decreasing([0.4, 0.3, 0.2, 0.1])
    assert sbc.strictly_decreasing([1, 0, -1, -3, -5])

    # Test non-strictly decreasing sequences
    assert not sbc.strictly_decreasing([5, 4, 4, 2, 1])
    assert not sbc.strictly_decreasing([5, 4, 3, 4, 1])
    assert not sbc.strictly_decreasing([1, 2, 3, 4, 5])

    # Test empty and single element
    assert sbc.strictly_decreasing([])
    assert sbc.strictly_decreasing([1])


def test_merge_dictionary():
    """Test the merge_dictionary function."""
    from sambuca_core.utility.collections import merge_dictionary

    # Test basic merge
    dict1 = {'a': 1, 'b': 2}
    dict2 = {'c': 3, 'd': 4}
    result = merge_dictionary(dict1, dict2)
    expected = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
    assert result == expected

    # Test merge with overlapping keys (existing keys should not be modified)
    dict1 = {'a': 1, 'b': 2, 'c': 3}
    dict2 = {'c': 30, 'd': 4}
    result = merge_dictionary(dict1, dict2)
    expected = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
    assert result == expected

    # Test that the target dictionary is modified in-place
    dict1 = {'a': 1}
    dict2 = {'b': 2}
    result = merge_dictionary(dict1, dict2)
    assert result is dict1
    assert dict1 == {'a': 1, 'b': 2}


def test_pairwise():
    """Test the pairwise function."""
    from sambuca_core.utility.collections import pairwise

    # Test basic usage
    result = list(pairwise([1, 2, 3, 4]))
    expected = [(1, 2), (2, 3), (3, 4)]
    assert result == expected

    # Test with strings
    result = list(pairwise('ABCD'))
    expected = [('A', 'B'), ('B', 'C'), ('C', 'D')]
    assert result == expected

    # Test with empty and single element
    assert list(pairwise([])) == []
    assert list(pairwise([1])) == []


def test_list_files():
    """Test the list_files function."""
    # Create a temporary directory with some test files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        files = [
            'test1.txt',
            'test2.txt',
            'data.csv',
            'config.json',
            'image.png',
            'script.py'
        ]

        for file in files:
            Path(temp_dir, file).touch()

        # Test listing all files
        result = sbc.utility.list_files(temp_dir)
        assert len(result) == len(files)
        assert all(os.path.isfile(f) for f in result)

        # Test filtering by extension
        txt_files = sbc.utility.list_files(temp_dir, extensions=['txt'])
        assert len(txt_files) == 2
        assert all(f.endswith('.txt') for f in txt_files)

        # Test multiple extensions
        text_and_code_files = sbc.utility.list_files(temp_dir, extensions=['txt', 'py'])
        assert len(text_and_code_files) == 3
        assert all(f.endswith(('.txt', '.py')) for f in text_and_code_files)

        # Test with no matching files
        no_files = sbc.utility.list_files(temp_dir, extensions=['docx'])
        assert len(no_files) == 0

        # Test nonexistent directory
        with pytest.raises(OSError):
            sbc.utility.list_files(os.path.join(temp_dir, 'nonexistent'))