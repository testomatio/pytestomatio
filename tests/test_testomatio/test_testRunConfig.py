import pytest
import os
from unittest.mock import patch, mock_open

from pytestomatio.testomatio.testRunConfig import TestRunConfig, TESTOMATIO_TEST_RUN_LOCK_FILE


class TestTestRunConfig:
    """Tests for TestRunConfig class"""

    def test_init_default_values(self):
        """Test init with default values"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('pytestomatio.testomatio.testRunConfig.dt.datetime') as mock_dt:
                mock_dt.now.return_value.strftime.return_value = "2024-01-15 10:30:45"

                config = TestRunConfig()

                assert config.access_event is None
                assert config.test_run_id is None
                assert config.title == "test run at 2024-01-15 10:30:45"
                assert config.environment is None
                assert config.label is None
                assert config.group_title is None
                assert config.parallel is True
                assert config.shared_run is False
                assert config.status_request == {}
                assert config.meta is None

    def test_init_with_env_variables(self):
        """Test init with env vars"""
        env_vars = {
            'TESTOMATIO_RUN_ID': 'run_12345',
            'TESTOMATIO_TITLE': 'Custom Test Run',
            'TESTOMATIO_ENV': 'linux,browser:chrome,1920x1080',
            'TESTOMATIO_LABEL': 'smoke,regression',
            'TESTOMATIO_RUNGROUP_TITLE': 'Release 2.0',
            'TESTOMATIO_PUBLISH': '1'
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = TestRunConfig()

            assert config.access_event == 'publish'
            assert config.test_run_id == 'run_12345'
            assert config.title == 'Custom Test Run'
            assert config.environment == 'linux,browser:chrome,1920x1080'
            assert config.label == 'smoke,regression'
            assert config.group_title == 'Release 2.0'
            assert config.parallel is True
            assert config.shared_run is False
            assert config.meta == {'linux': None, 'browser': 'chrome', '1920x1080': None}

    @pytest.mark.parametrize('value', ['True', 'true', '1'])
    def test_init_shared_run_true_variations(self, value):
        """Test different true values for TESTOMATIO_SHARED_RUN"""
        with patch.dict(os.environ, {'TESTOMATIO_SHARED_RUN': value}, clear=True):
            config = TestRunConfig()

            assert config.shared_run is True
            assert config.parallel is False

    @pytest.mark.parametrize('value', ['False', 'false', '0', 'anything'])
    def test_init_shared_run_false_variations(self, value):
        """Test different false values TESTOMATIO_SHARED_RUN"""
        with patch.dict(os.environ, {'TESTOMATIO_SHARED_RUN': value}, clear=True):
            config = TestRunConfig()

            assert config.shared_run is False
            assert config.parallel is True

    def test_to_dict_full_data(self):
        """Test to_dict with full data"""
        env_vars = {
            'TESTOMATIO_RUN_ID': 'run_123',
            'TESTOMATIO_TITLE': 'Test Run',
            'TESTOMATIO_ENV': 'env1,env2',
            'TESTOMATIO_LABEL': 'label1,label2',
            'TESTOMATIO_RUNGROUP_TITLE': 'Group 1',
            'TESTOMATIO_SHARED_RUN': 'true',
            'TESTOMATIO_PUBLISH': 'true'
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = TestRunConfig()

            result = config.to_dict()

            expected = {
                'id': 'run_123',
                'access_event': 'publish',
                'title': 'Test Run',
                'group_title': 'Group 1',
                'env': 'env1,env2',
                'label': 'label1,label2',
                'parallel': False,
                'shared_run': True,
                'ci_build_url': None
            }

            assert result == expected

    def test_to_dict_without_run_id(self):
        """Test to_dict without run_id"""
        with patch.dict(os.environ, {'TESTOMATIO_TITLE': 'No ID Run'}, clear=True):
            config = TestRunConfig()

            result = config.to_dict()

            assert 'id' not in result
            assert result['title'] == 'No ID Run'

    def test_set_env(self):
        """Test set_env"""
        config = TestRunConfig()

        config.set_env('new_env, with spaces ')

        assert config.environment == 'new_env,withspaces'

    @patch('tempfile.gettempdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_run_id(self, mock_file, mock_temp_dir):
        """Test run_id saved to file"""
        mock_temp_dir.return_value = '/tmp'

        config = TestRunConfig()
        config.save_run_id('new_run_123')

        assert config.test_run_id == 'new_run_123'

        expected_path = f'/tmp/{TESTOMATIO_TEST_RUN_LOCK_FILE}'
        mock_file.assert_called_once_with(expected_path, 'w')
        mock_file().write.assert_called_once_with('new_run_123')

    @patch('tempfile.gettempdir')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='saved_run_456')
    def test_get_run_id_from_file(self, mock_file, mock_exists, mock_temp_dir):
        """Test get run_id from file"""
        mock_temp_dir.return_value = '/tmp'
        mock_exists.return_value = True

        config = TestRunConfig()
        config.test_run_id = None

        result = config.get_run_id()

        assert result == 'saved_run_456'
        assert config.test_run_id == 'saved_run_456'

        expected_path = f'/tmp/{TESTOMATIO_TEST_RUN_LOCK_FILE}'
        mock_file.assert_called_once_with(expected_path, 'r')

    @patch('tempfile.gettempdir')
    @patch('os.path.exists')
    def test_get_run_id(self, mock_exists, mock_temp_dir):
        """Тest get run_id"""
        config = TestRunConfig()
        config.test_run_id = 'memory_run_789'

        result = config.get_run_id()

        assert result == 'memory_run_789'
        mock_exists.assert_not_called()

    @patch('tempfile.gettempdir')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_clear_run_id_file(self, mock_remove, mock_exists, mock_temp_dir):
        """Test remove run_id file"""
        mock_temp_dir.return_value = '/tmp'
        mock_exists.return_value = True

        config = TestRunConfig()
        config.clear_run_id()

        expected_path = f'/tmp/{TESTOMATIO_TEST_RUN_LOCK_FILE}'
        mock_remove.assert_called_once_with(expected_path)

    def test_resolve_build_url_downstream_mode(self):
        """Test resolve_build_url in downstream mode"""
        with patch.dict(os.environ, {'TESTOMATIO_CI_DOWNSTREAM': 'true'}, clear=True):
            config = TestRunConfig()

            assert config.build_url is None

    def test_resolve_build_url_jenkins(self):
        """Test resolve_build_url for Jenkins"""
        with patch.dict(os.environ, {'BUILD_URL': 'https://jenkins.com/job/test/123'}, clear=True):
            config = TestRunConfig()

            assert config.build_url == 'https://jenkins.com/job/test/123'

    def test_resolve_build_url_github_actions(self):
        """Test resolve_build_url for GitHub Actions"""
        github_env = {
            'GITHUB_RUN_ID': '987654321',
            'GITHUB_SERVER_URL': 'https://github.com',
            'GITHUB_REPOSITORY': 'user/repo'
        }

        with patch.dict(os.environ, github_env, clear=True):
            config = TestRunConfig()

            expected = 'https://github.com/user/repo/actions/runs/987654321'
            assert config.build_url == expected

    def test_resolve_build_url_azure_devops(self):
        """Test resolve_build_url for Azure DevOps"""
        azure_env = {
            'SYSTEM_TEAMFOUNDATIONCOLLECTIONURI': 'https://dev.azure.com/org',
            'SYSTEM_TEAMPROJECT': 'MyProject',
            'BUILD_BUILDID': '12345'
        }

        with patch.dict(os.environ, azure_env, clear=True):
            config = TestRunConfig()

            expected = 'https://dev.azure.com/org/MyProject/_build/results?buildId=12345'
            assert config.build_url == expected

    def test_resolve_build_url_priority(self):
        """Test source priority"""
        env_vars = {
            'BUILD_URL': 'https://jenkins.com/job/1',
            'CI_JOB_URL': 'https://gitlab.com/job/2',
            'CIRCLE_BUILD_URL': 'https://circle.com/job/3'
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = TestRunConfig()

            assert config.build_url == 'https://jenkins.com/job/1'

    def test_resolve_build_url_invalid_without_http(self):
        """Test build_url without http"""
        with patch.dict(os.environ, {'BUILD_URL': 'ftp://invalid.com/build'}, clear=True):
            config = TestRunConfig()

            assert config.build_url is None

    def test_resolve_build_url_no_sources(self):
        """Test no source for build_url"""
        with patch.dict(os.environ, {}, clear=True):
            config = TestRunConfig()

            assert config.build_url is None

    def test_update_meta(self):
        """Test update_meta"""
        with patch.dict(os.environ, {}, clear=True):
            config = TestRunConfig()
            assert config.meta is None

            config.environment = 'env1, env2:True'
            result = config.update_meta()
            assert result == {' env2': 'True', 'env1': None}
