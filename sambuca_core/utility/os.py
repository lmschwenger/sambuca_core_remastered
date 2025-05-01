"""OS utility functions."""

import os
from typing import List, Optional


def list_files(directory: str, extensions: Optional[List[str]] = None) -> List[str]:
    """Lists all files with the specified extensions.

    Args:
        directory: The directory to search.
        extensions: Optional list of extensions to filter by (without the leading '.').

    Returns:
        List of full file paths.

    Raises:
        OSError: If the directory does not exist.
    """
    if not os.path.isdir(directory):
        raise OSError(f"Directory {directory} does not exist.")

    file_list = []

    # Normalize the extensions (convert to lowercase, ensure no leading dots)
    if extensions:
        extensions = [ext.lower().lstrip('.') for ext in extensions]

    for file in os.listdir(directory):
        full_path = os.path.join(directory, file)
        if os.path.isfile(full_path):
            if extensions:
                _, ext = os.path.splitext(file)
                if ext.lower().lstrip('.') in extensions:
                    file_list.append(full_path)
            else:
                file_list.append(full_path)

    return file_list