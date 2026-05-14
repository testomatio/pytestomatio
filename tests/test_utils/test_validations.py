import pytest
import os
from unittest.mock import Mock, patch
from _pytest.config.exceptions import UsageError

from pytestomatio.utils.constants import RUN_KINDS
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

    def test_validate_option_returns_none_when_no_option(self, mock_config: Mock):
        """Test return None when testomatio option not set"""
        mock_config.getoption.return_value = None

        result = validate_option(mock_config)

        assert result is None
        assert 'testomatio' in mock_config.mock_calls[0].args

    @pytest.mark.parametrize("option_value", ['sync', 'report', 'remove', 'launch', 'finish'])
    def test_validate_option_raises_error_when_no_testomatio_env(self, mock_config, option_value):
        """Test ValueError raised when no TESTOMATIO env"""
        mock_config.getoption.return_value = option_value

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match='TESTOMATIO env variable is not set'):
                validate_option(mock_config)

    @pytest.mark.parametrize("option_value", ['sync', 'report', 'remove'])
    def test_validate_option_passes_when_testomatio_env_set(self, mock_config, option_value):
        """Test TESTOMATIO env validation passes"""
        mock_config.getoption.side_effect = lambda opt: option_value if opt == 'testomatio' else None

        with patch.dict(os.environ, {'TESTOMATIO': 'test_token_123'}):
            result = validate_option(mock_config)

        assert result == option_value

    def test_validate_option_debug_doesnt_require_testomatio_env(self, mock_config):
        """Test debug option doesnt require TESTOMATIO env"""
        mock_config.getoption.side_effect = lambda opt: 'debug' if opt == 'testomatio' else None

        with patch.dict(os.environ, {}, clear=True):
            result = validate_option(mock_config)

        assert result == 'debug'

    def test_validate_launch_option_requires_api_key(self, mock_config):
        """Test validation failed if no api key for launch option"""
        mock_config.getoption.return_value = 'launch'

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match='TESTOMATIO env variable is not set'):
                validate_option(mock_config)

    @pytest.mark.parametrize("run_kind", RUN_KINDS)
    def test_validate_launch_option_can_be_used_with_kind_option(self, mock_config, run_kind):
        """Test validation passes for launch option when run kind specified"""
        options = {'testomatio': 'launch', 'kind': run_kind}
        mock_config.getoption.side_effect = lambda opt: options.get(opt)

        with patch.dict(os.environ, {'TESTOMATIO': 'test_token_123'}, clear=True):
            result = validate_option(mock_config)

        assert result == 'launch'

    def test_validate_launch_option_can_be_used_without_kind_option(self, mock_config):
        """Test validation passes for launch option if kind not specified"""
        options = {'testomatio': 'launch', 'kind': None}
        mock_config.getoption.side_effect = lambda opt: options.get(opt)

        with patch.dict(os.environ, {'TESTOMATIO': 'test_token_123'}, clear=True):
            result = validate_option(mock_config)

        assert result == 'launch'

    @pytest.mark.parametrize("run_kind", ['Incorrect_type', 'half-manual'])
    def test_validate_launch_option_raises_error_if_incorrect_kind(self, mock_config, run_kind):
        """Test validation not passed if incorrect testrun kind"""
        options = {'testomatio': 'launch', 'kind': run_kind}
        mock_config.getoption.side_effect = lambda opt: options.get(opt)

        with patch.dict(os.environ, {'TESTOMATIO': 'test_token_123'}, clear=True):
            with pytest.raises(ValueError, match=f"Not supported run kind. Choose one of next kinds: \\({RUN_KINDS}\\)"):
                validate_option(mock_config)

    @pytest.mark.parametrize("run_kind", RUN_KINDS)
    @pytest.mark.parametrize("testomatio_option", ['sync', 'report', 'remove', 'debug', 'finish'])
    def test_validate_kind_option_can_be_used_only_with_launch_option(self, mock_config, run_kind, testomatio_option):
        """Test error raised if kind option used without launch option"""
        options = {'testomatio': testomatio_option, 'kind': run_kind}
        mock_config.getoption.side_effect = lambda opt: options.get(opt)

        with patch.dict(os.environ, {'TESTOMATIO': 'test_token_123', 'TESTOMATIO_RUN': 're23a'}, clear=True):
            with pytest.raises(ValueError, match="You can choose run kind only for 'launch' option"):
                validate_option(mock_config)

    def test_validate_finish_option_requires_api_key(self, mock_config):
        """Test validation failed if no api key for finish option"""
        mock_config.getoption.return_value = 'launch'

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match='TESTOMATIO env variable is not set'):
                validate_option(mock_config)

    def test_validate_launch_option_error_if_run_id_set(self, mock_config):
        """Test validation for launch option failed if test run id set"""
        mock_config.getoption.return_value = 'launch'

        with patch.dict(os.environ, {'TESTOMATIO': 'ds', 'TESTOMATIO_RUN': "asd"}, clear=True):
            with pytest.raises(ValueError, match='Test Run id was passed. Please unset TESTOMATIO_RUN_ID or TESTOMATIO_RUN env variablses to create an empty run'):
                validate_option(mock_config)

    def test_validate_finish_option_error_if_run_id_not_set(self, mock_config):
        """Test validation for finish option failed if test run id not set"""
        mock_config.getoption.return_value = 'finish'

        with patch.dict(os.environ, {'TESTOMATIO': 'ds'}, clear=True):
            with pytest.raises(ValueError, match='TESTOMATIO_RUN_ID env variable is not set'):
                validate_option(mock_config)

    def test_validate_option_unknown_option_passes_through(self, mock_config):
        """Test unknown options passes through"""
        mock_config.getoption.side_effect = lambda opt: 'unknown_option' if opt == 'testomatio' else None

        with patch.dict(os.environ, {}, clear=True):
            result = validate_option(mock_config)

        assert result == 'unknown_option'

    def test_validate_option_no_xdist_plugin_passes(self, mock_config):
        """Test validation without xdist plugin successful"""
        mock_config.getoption.side_effect = lambda opt: 'sync' if opt == 'testomatio' else None
        mock_config.pluginmanager.getplugin.return_value = None

        with patch.dict(os.environ, {'TESTOMATIO': 'test_token'}):
            result = validate_option(mock_config)

        assert result == 'sync'
        mock_config.pluginmanager.getplugin.assert_called_once_with('xdist')

    @pytest.mark.parametrize("option_value", ['sync', 'debug', 'remove'])
    def test_validate_option_xdist_with_zero_processes_passes(self, mock_config, option_value):
        """Test xdist with 0 processes pass validation """
        mock_config.getoption.side_effect = lambda opt: option_value if opt == 'testomatio' else None
        mock_config.pluginmanager.getplugin.return_value = Mock()
        mock_config.option.numprocesses = 0

        with patch.dict(os.environ, {'TESTOMATIO': 'test_token'}):
            result = validate_option(mock_config)

        assert not result

    @pytest.mark.parametrize("option_value", ['sync', 'debug', 'remove'])
    @pytest.mark.parametrize("num_processes", [1, 2, 4, 8])
    def test_validate_option_xdist_with_parallel_processes_raises_error(self, mock_config, option_value, num_processes):
        """Test xdist with і > 0 processes raise UsageError"""
        mock_config.getoption.side_effect = lambda opt: option_value if opt == 'testomatio' else None
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
        mock_config.getoption.side_effect = lambda opt: 'report' if opt == 'testomatio' else None
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