"""Unit tests for sambuca.core.data_fetchers module."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from sambuca.core.data_fetchers.base import BaseDataFetcher


class TestBaseDataFetcher:
    """Test the abstract base data fetcher."""

    def setup_method(self):
        """Set up test fixtures."""

        class TestDataFetcher(BaseDataFetcher):
            @property
            def name(self):
                return "test_fetcher"

            @property
            def supported_parameters(self):
                return ["param1", "param2", "param3"]

            @property
            def required_dependencies(self):
                return ["numpy", "requests"]

            def is_available(self):
                return True

            def fetch_data(self, aoi, date, parameters=None, output_dir=None, **kwargs):
                return {"param1": "/path/to/param1.tif", "param2": "/path/to/param2.tif"}

        self.fetcher = TestDataFetcher()

    def test_abstract_properties(self):
        """Test that abstract properties are implemented."""
        assert self.fetcher.name == "test_fetcher"
        assert self.fetcher.supported_parameters == ["param1", "param2", "param3"]
        assert self.fetcher.required_dependencies == ["numpy", "requests"]
        assert self.fetcher.is_available() is True

    def test_fetch_data_interface(self):
        """Test the fetch_data interface."""
        result = self.fetcher.fetch_data(
            aoi="test_aoi",
            date="2023-01-01",
            parameters=["param1", "param2"]
        )

        assert isinstance(result, dict)
        assert "param1" in result
        assert "param2" in result

    def test_validate_parameters_valid(self):
        """Test parameter validation with valid parameters."""
        self.fetcher.validate_parameters(["param1", "param2"])
        self.fetcher.validate_parameters(["param1"])
        self.fetcher.validate_parameters([])
        self.fetcher.validate_parameters(None)

    def test_validate_parameters_invalid(self):
        """Test parameter validation with invalid parameters."""
        with pytest.raises(ValueError, match="Unsupported parameters"):
            self.fetcher.validate_parameters(["invalid_param"])

        with pytest.raises(ValueError, match="Unsupported parameters"):
            self.fetcher.validate_parameters(["param1", "invalid_param"])

    def test_validate_parameters_error_message(self):
        """Test that validation error includes helpful information."""
        try:
            self.fetcher.validate_parameters(["invalid1", "invalid2"])
        except ValueError as e:
            error_msg = str(e)
            assert "invalid1" in error_msg
            assert "invalid2" in error_msg
            assert "param1, param2, param3" in error_msg


class TestDataFetcherErrorHandling:
    """Test error handling in data fetchers."""

    def test_fetcher_error_handling(self):
        """Test fetcher error handling."""

        class ErrorFetcher(BaseDataFetcher):
            @property
            def name(self):
                return "error_fetcher"

            @property
            def supported_parameters(self):
                return ["error_param"]

            @property
            def required_dependencies(self):
                return []

            def is_available(self):
                return True

            def fetch_data(self, aoi, date, parameters=None, output_dir=None, **kwargs):
                raise ConnectionError("Network error")

        fetcher = ErrorFetcher()

        with pytest.raises(ConnectionError, match="Network error"):
            fetcher.fetch_data(
                aoi="test",
                date="2023-01-01"
            )

    def test_dependency_availability_check(self):
        """Test dependency availability checking."""

        class DependentFetcher(BaseDataFetcher):
            @property
            def name(self):
                return "dependent_fetcher"

            @property
            def supported_parameters(self):
                return ["param1"]

            @property
            def required_dependencies(self):
                return ["nonexistent_package"]

            def is_available(self):
                try:
                    import nonexistent_package
                    return True
                except ImportError:
                    return False

            def fetch_data(self, aoi, date, parameters=None, output_dir=None, **kwargs):
                if not self.is_available():
                    raise ImportError("Required dependencies not available")
                return {}

        fetcher = DependentFetcher()
        assert fetcher.is_available() is False

        with pytest.raises(ImportError):
            fetcher.fetch_data("test", "2023-01-01")


class TestDataFetcherIntegration:
    """Integration tests for data fetchers."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_output_directory_creation(self):
        """Test that fetchers can create output directories."""

        class DirectoryFetcher(BaseDataFetcher):
            @property
            def name(self):
                return "dir_fetcher"

            @property
            def supported_parameters(self):
                return ["test"]

            @property
            def required_dependencies(self):
                return []

            def is_available(self):
                return True

            def fetch_data(self, aoi, date, parameters=None, output_dir=None, **kwargs):
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

                test_file = output_path / "test_output.txt"
                test_file.write_text("test data")

                return {"test": str(test_file)}

        fetcher = DirectoryFetcher()
        new_dir = Path(self.temp_dir) / "new_subdir"

        result = fetcher.fetch_data(
            aoi="test",
            date="2023-01-01",
            output_dir=str(new_dir)
        )

        assert new_dir.exists()
        assert Path(result["test"]).exists()
        assert Path(result["test"]).read_text() == "test data"

    @patch('requests.get')
    def test_fetcher_with_mock_api(self, mock_get):
        """Test fetcher with mocked API calls."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"mock_data"
        mock_get.return_value = mock_response

        class MockAPIFetcher(BaseDataFetcher):
            @property
            def name(self):
                return "mock_api"

            @property
            def supported_parameters(self):
                return ["test_param"]

            @property
            def required_dependencies(self):
                return ["requests"]

            def is_available(self):
                return True

            def fetch_data(self, aoi, date, parameters=None, output_dir=None, **kwargs):
                import requests
                response = requests.get("https://mock-api.com/data")

                if response.status_code == 200:
                    output_path = Path(output_dir) / "test_data.txt"
                    output_path.write_bytes(response.content)
                    return {"test_param": str(output_path)}
                else:
                    raise Exception("API request failed")

        fetcher = MockAPIFetcher()
        result = fetcher.fetch_data(
            aoi="test",
            date="2023-01-01",
            parameters=["test_param"],
            output_dir=self.temp_dir
        )

        assert "test_param" in result
        assert Path(result["test_param"]).exists()
        mock_get.assert_called_once_with("https://mock-api.com/data")
