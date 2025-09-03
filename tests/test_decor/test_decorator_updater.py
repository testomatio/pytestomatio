import os
from unittest.mock import patch

from pytestomatio.decor.decorator_updater import update_tests


class TestUpdateTests:
    """Test for update_tests"""

    @patch('pytestomatio.decor.decorator_updater.update_tests_default')
    @patch('pytestomatio.decor.decorator_updater.update_tests_pep8')
    def test_update_tests_default_style(self, mock_pep8, mock_default):
        """Test usage with default style"""
        with patch.dict(os.environ, {}, clear=True):
            update_tests(
                file="test_file.py",
                mapped_tests=[("test1", "@T123"), ("test2", "@T456")],
                all_tests=["test1", "test2"],
                decorator_name="testomatio",
                remove=False
            )

            mock_default.assert_called_once_with(
                "test_file.py",
                [("test1", "@T123"), ("test2", "@T456")],
                ["test1", "test2"],
                "testomatio",
                False
            )
            mock_pep8.assert_not_called()

    @patch('pytestomatio.decor.decorator_updater.update_tests_default')
    @patch('pytestomatio.decor.decorator_updater.update_tests_pep8')
    def test_update_tests_pep8_style(self, mock_pep8, mock_default):
        """Test usage pep8 style"""
        with patch.dict(os.environ, {'TESTOMATIO_CODE_STYLE': 'pep8'}):
            update_tests(
                file="test_file.py",
                mapped_tests=[("test1", "@T123")],
                all_tests=["test1"],
                decorator_name="testomatio",
                remove=True
            )

            mock_pep8.assert_called_once_with(
                "test_file.py",
                [("test1", "@T123")],
                ["test1"],
                "testomatio",
                True
            )
            mock_default.assert_not_called()

    @patch('pytestomatio.decor.decorator_updater.update_tests_default')
    @patch('pytestomatio.decor.decorator_updater.update_tests_pep8')
    def test_update_tests_unknown_style_defaults_to_default(self, mock_pep8, mock_default):
        """Test if unknown style passed, default will be used"""
        with patch.dict(os.environ, {'TESTOMATIO_CODE_STYLE': 'unknown_style'}):
            update_tests(
                file="test_file.py",
                mapped_tests=[("test", "id")],
                all_tests=["test"],
                decorator_name="testomatio"
            )

            mock_default.assert_called_once()
            mock_pep8.assert_not_called()
