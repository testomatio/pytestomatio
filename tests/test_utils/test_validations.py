import pytest
import os
from unittest.mock import Mock, patch
from _pytest.config.exceptions import UsageError

from pytestomatio.utils.validations import validate_option


class TestValidateOption:
    """Tests for validate_option function"""

    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.getoption.return_value = None
        config.pluginmanager = Mock()
        config.pluginmanager.getplugin.return_value = None
        config.option = Mock()
        config.option.numprocesses = 0
        return config

    def test_validate_option_returns_none_when_no_option(self, mock_config):
        """Test return None when testomatio option not set"""
        mock_config.getoption.return_value = None

        result = validate_option(mock_config)

        assert result is None
        mock_config.getoption.assert_called_once_with('testomatio')

    @pytest.mark.parametrize("option_value", ['sync', 'report', 'remove'])
    def test_validate_option_raises_error_when_no_testomatio_env(self, mock_config, option_value):
        """Test ValueError raised when no TESTOMATIO env"""
        mock_config.getoption.return_value = option_value

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match='TESTOMATIO env variable is not set'):
                validate_option(mock_config)

    @pytest.mark.parametrize("option_value", ['sync', 'report', 'remove'])
    def test_validate_option_passes_when_testomatio_env_set(self, mock_config, option_value):
        """Test TESTOMATIO env validation passes"""
        mock_config.getoption.return_value = option_value

        with patch.dict(os.environ, {'TESTOMATIO': 'test_token_123'}):
            result = validate_option(mock_config)

        assert result == option_value

    def test_validate_option_debug_doesnt_require_testomatio_env(self, mock_config):
        """Test debug option doesnt require TESTOMATIO env"""
        mock_config.getoption.return_value = 'debug'

        with patch.dict(os.environ, {}, clear=True):
            result = validate_option(mock_config)

        assert result == 'debug'

    def test_validate_option_unknown_option_passes_through(self, mock_config):
        """Test unknown options passes through"""
        mock_config.getoption.return_value = 'unknown_option'

        with patch.dict(os.environ, {}, clear=True):
            result = validate_option(mock_config)

        assert result == 'unknown_option'

    def test_validate_option_no_xdist_plugin_passes(self, mock_config):
        """Test validation without xdist plugin successful"""
        mock_config.getoption.return_value = 'sync'
        mock_config.pluginmanager.getplugin.return_value = None

        with patch.dict(os.environ, {'TESTOMATIO': 'test_token'}):
            result = validate_option(mock_config)

        assert result == 'sync'
        mock_config.pluginmanager.getplugin.assert_called_once_with('xdist')

    @pytest.mark.parametrize("option_value", ['sync', 'debug', 'remove'])
    def test_validate_option_xdist_with_zero_processes_passes(self, mock_config, option_value):
        """Test xdist with 0 processes pass validation """
        mock_config.getoption.return_value = option_value
        mock_config.pluginmanager.getplugin.return_value = Mock()
        mock_config.option.numprocesses = 0

        with patch.dict(os.environ, {'TESTOMATIO': 'test_token'}):
            result = validate_option(mock_config)

        assert not result

    @pytest.mark.parametrize("option_value", ['sync', 'debug', 'remove'])
    @pytest.mark.parametrize("num_processes", [1, 2, 4, 8])
    def test_validate_option_xdist_with_parallel_processes_raises_error(self, mock_config, option_value, num_processes):
        """Test xdist with і > 0 processes raise UsageError"""
        mock_config.getoption.return_value = option_value
        mock_config.pluginmanager.getplugin.return_value = Mock()
        mock_config.option.numprocesses = num_processes

        env_dict = {'TESTOMATIO': 'test_token'} if option_value != 'debug' else {}

        with patch.dict(os.environ, env_dict):
            with pytest.raises(UsageError) as exc_info:
                validate_option(mock_config)

            error_message = str(exc_info.value)
            assert "sync" in error_message.lower()
            assert "parallel execution" in error_message.lower()
            assert "-n 0" in error_message

    def test_validate_option_report_with_xdist_parallel_passes(self, mock_config):
        """Test report mode works with xdist"""
        mock_config.getoption.return_value = 'report'
        mock_config.pluginmanager.getplugin.return_value = Mock()
        mock_config.option.numprocesses = 4

        with patch.dict(os.environ, {'TESTOMATIO': 'test_token'}):
            result = validate_option(mock_config)

        assert result == 'report'

    def test_validate_option_empty_string_treated_as_none(self, mock_config):
        """Test empty string as option value treated as None"""
        mock_config.getoption.return_value = ''

        result = validate_option(mock_config)

        assert result is None