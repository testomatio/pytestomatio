import pytest
from unittest.mock import Mock, patch
import requests
from requests.exceptions import HTTPError, ConnectionError
import os

from pytestomatio.connect.connector import Connector
from pytestomatio.testing.testItem import TestItem


class TestConnector:
    """Tests for Connector"""

    @pytest.fixture
    def connector(self):
        return Connector("https://api.testomat.io", "test_api_key_123")

    def test_init_basic(self):
        """Test init Connector"""
        connector = Connector("https://example.com", "api_key")

        assert connector.base_url == "https://example.com"
        assert connector.api_key == "api_key"
        assert connector.jwt == ""
        assert isinstance(connector._session, requests.Session)

    @patch.dict(os.environ, {}, clear=True)
    def test_apply_proxy_settings_no_proxy(self, connector):
        """Test config without proxy"""
        with patch.object(connector, '_test_proxy_connection', return_value=True):
            connector._apply_proxy_settings()

            assert connector._session.proxies == {}
            assert connector._session.verify is True

    @patch.dict(os.environ, {'HTTP_PROXY': 'http://proxy.example.com:8080'})
    def test_apply_proxy_settings_with_proxy_working(self, connector):
        """Test config with working proxy"""
        with patch.object(connector, '_test_proxy_connection', return_value=True):
            connector._apply_proxy_settings()

            expected_proxies = {
                "http": "http://proxy.example.com:8080",
                "https": "http://proxy.example.com:8080"
            }
            assert connector._session.proxies == expected_proxies
            assert connector._session.verify is False

    @patch.dict(os.environ, {'HTTP_PROXY': 'http://proxy.example.com:8080'})
    def test_apply_proxy_settings_with_proxy_failing(self, connector):
        """Test fallback when proxies not working"""
        with patch.object(connector, '_test_proxy_connection', return_value=False):
            connector._apply_proxy_settings()

            assert connector._session.proxies == {}
            assert connector._session.verify is True

    @patch('requests.Session.get')
    def test_test_proxy_connection_success(self, mock_get, connector):
        """Test successful connection check"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = connector._test_proxy_connection(timeout=1)

        assert result is True
        assert mock_get.call_count == 1

    @patch('requests.Session.get')
    @patch('time.sleep')
    def test_test_proxy_connection_timeout(self, mock_sleep, mock_get, connector):
        """Test check connection timeout"""
        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")

        result = connector._test_proxy_connection(timeout=1, retry_interval=0.1)

        assert result is False
        assert mock_get.call_count > 1

    @patch('requests.Session.post')
    def test_load_tests_success(self, mock_post, connector):
        """Test successful load test"""
        mock_test = Mock(spec=TestItem)
        mock_test.sync_title = "Test Login"
        mock_test.class_name = "TestAuth"
        mock_test.source_code = "def test_login(): pass"
        mock_test.file_path = "test_auth.py"
        mock_test.file_name = "test_auth.py"
        mock_test.docstring = 'docstring'

        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {}, clear=True):
            connector.load_tests([mock_test])

        assert mock_post.call_count == 1
        call_args = mock_post.call_args

        assert f'{connector.base_url}/api/load' in call_args[0][0]
        assert 'api_key=test_api_key_123' in call_args[0][0]

        payload = call_args[1]['json']
        assert payload['framework'] == 'pytest'
        assert payload['language'] == 'python'
        assert len(payload['tests']) == 1
        assert payload['tests'][0]['name'] == 'Test Login'

    @patch('requests.Session.post')
    def test_load_tests_connection_error(self, mock_post, connector):
        """Test handling connection error on load_tests"""
        mock_post.side_effect = ConnectionError("Connection failed")

        result = connector.load_tests([])

        assert result is None

    @patch('requests.Session.get')
    @patch.object(Connector, '_apply_proxy_settings')
    def test_get_tests_success(self, mock_apply_proxy, mock_get, connector):
        """Тест успішного отримання тестів"""
        mock_response = Mock()
        mock_response.json.return_value = {"tests": {"test1": "@T123"}}
        mock_get.return_value = mock_response

        result = connector.get_tests([])

        mock_get.assert_called_once_with(f'{connector.base_url}/api/test_data?api_key={connector.api_key}')
        assert result == {"tests": {"test1": "@T123"}}

    @patch('requests.Session.post')
    def test_create_test_run_success(self, mock_post, connector):
        """Test that test run successfully created"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"uid": "run_123", "title": "Test Run"}
        mock_post.return_value = mock_response

        result = connector.create_test_run(
            title="Test Run",
            access_event="publish",
            group_title="Group 1",
            env="linux,chrome",
            label="smoke",
            shared_run=False,
            shared_run_timeout="2",
            parallel=True,
            ci_build_url="https://ci.example.com/build/123"
        )

        mock_post.assert_called_once_with(
            f'{connector.base_url}/api/reporter',
            json={
                "api_key": "test_api_key_123",
                "access_event": "publish",
                "title": "Test Run",
                "group_title": "Group 1",
                "env": "linux,chrome",
                "label": "smoke",
                "shared_run": False,
                "shared_run_timeout": "2",
                "parallel": True,
                "ci_build_url": "https://ci.example.com/build/123"
            }
        )

        assert result == {"uid": "run_123", "title": "Test Run"}

    @patch('requests.Session.post')
    def test_create_test_run_filters_none_values(self, mock_post, connector):
        """Test None values filtered"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"uid": "run_123"}
        mock_post.return_value = mock_response

        connector.create_test_run(
            title="Test Run",
            access_event=None,
            group_title=None,
            env=None,
            label="smoke",
            shared_run=False,
            shared_run_timeout=None,
            parallel=True,
            ci_build_url=None
        )

        payload = mock_post.call_args[1]['json']
        expected_payload = {
            "api_key": "test_api_key_123",
            "title": "Test Run",
            "label": "smoke",
            "shared_run": False,
            "parallel": True
        }
        assert payload == expected_payload

    @patch('requests.Session.post')
    def test_create_test_run_http_error(self, mock_post, connector):
        """Test HTTP error handled wher create test run"""
        mock_post.side_effect = HTTPError("HTTP Error")

        result = connector.create_test_run("Test", None, None, None, None, False, True, None, None)
        assert result is None

    @patch('requests.Session.put')
    def test_update_test_run_success(self, mock_put, connector):
        """Test successful update test run"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"uid": "run_123"}
        mock_put.return_value = mock_response

        result = connector.update_test_run(
            id="run_123",
            access_event='publish',
            title="Updated Run",
            group_title="Group",
            env="windows",
            label="regression",
            shared_run=True,
            shared_run_timeout='2',
            parallel=False,
            ci_build_url="https://ci.example.com"
        )

        mock_put.assert_called_once_with(
            f'{connector.base_url}/api/reporter/run_123',
            json={
                "access_event": "publish",
                "api_key": "test_api_key_123",
                "title": "Updated Run",
                "group_title": "Group",
                "env": "windows",
                "label": "regression",
                "shared_run": True,
                "shared_run_timeout": '2',
                "parallel": False,
                "ci_build_url": "https://ci.example.com"
            }
        )

        assert result == {"uid": "run_123"}

    @patch('requests.Session.post')
    def test_update_test_status_success(self, mock_post, connector):
        """Test successful test status update"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        connector.update_test_status(
            run_id="run_123",
            rid="rid123",
            status="passed",
            title="Test Login",
            create=True,
            suite_title="Auth Suite",
            suite_id="suite_456",
            test_id="test_789",
            message=None,
            stack=None,
            run_time=1.5,
            artifacts=["screenshot.png"],
            steps="Step 1\nStep 2",
            code="def test_login(): pass",
            example={"param": "value"},
            overwrite=True,
            meta={}
        )

        assert mock_post.call_count == 1
        call_args = mock_post.call_args

        assert f'{connector.base_url}/api/reporter/run_123/testrun' in call_args[0][0]

        payload = call_args[1]['json']
        assert payload['create']
        assert payload['status'] == 'passed'
        assert payload['title'] == 'Test Login'
        assert payload['run_time'] == 1.5
        assert payload['artifacts'] == ["screenshot.png"]
        assert payload['code'] == "def test_login(): pass"
        assert payload['overwrite'] is True
        assert 'message' not in payload

    @patch('requests.Session.post')
    def test_update_test_status_filters_none_values(self, mock_post, connector):
        """Test update test status filters keys with none value"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        connector.update_test_status(
            run_id="run_123",
            status="passed",
            title="Test Login",
            create=None,
            suite_title="Auth Suite",
            suite_id="suite_456",
            test_id="test_789",
            message=None,
            stack=None,
            run_time=1.5,
            artifacts=["screenshot.png"],
            steps="Step 1\nStep 2",
            code=None,
            example={"param": "value"},
            overwrite=None,
            rid=None,
            meta=None
        )

        assert mock_post.call_count == 1
        call_args = mock_post.call_args

        assert f'{connector.base_url}/api/reporter/run_123/testrun' in call_args[0][0]

        payload = call_args[1]['json']
        assert payload['status'] == 'passed'
        assert payload['title'] == 'Test Login'
        assert payload['run_time'] == 1.5
        assert payload['artifacts'] == ["screenshot.png"]
        assert 'message' not in payload
        assert 'create' not in payload
        assert 'code' not in payload
        assert 'overwrite' not in payload

    @patch('requests.Session.put')
    def test_finish_test_run_final(self, mock_put, connector):
        """Test finish test run"""
        connector.finish_test_run("run_123", is_final=True)

        mock_put.assert_called_once_with(
            f'{connector.base_url}/api/reporter/run_123?api_key={connector.api_key}',
            json={"status_event": "finish_parallel"}
        )

    @patch('requests.Session.put')
    def test_finish_test_run_not_final(self, mock_put, connector):
        """Test successful finish not final test run"""
        connector.finish_test_run("run_123", is_final=False)

        mock_put.assert_called_once_with(
            f'{connector.base_url}/api/reporter/run_123?api_key={connector.api_key}',
            json={"status_event": "finish"}
        )

    @patch('requests.Session.put')
    def test_finish_test_run_connection_error(self, mock_put, connector):
        """Test handling connection error when finish test run"""
        mock_put.side_effect = ConnectionError("Connection failed")

        result = connector.finish_test_run("run_123")
        assert result is None

    def test_disconnect(self, connector):
        """Test session closed"""
        with patch.object(connector._session, 'close') as mock_close:
            connector.disconnect()
            assert mock_close.call_count == 1

    def test_session_property_getter(self, connector):
        """Test getter for session property"""
        with patch.object(connector, '_apply_proxy_settings') as mock_apply:
            session = connector.session

            assert session is connector._session
            assert mock_apply.call_count == 1

    def test_session_property_setter(self, connector):
        """Test setter for session property"""
        new_session = requests.Session()

        with patch.object(connector, '_apply_proxy_settings') as mock_apply:
            connector.session = new_session

            assert connector._session is new_session
            assert mock_apply.call_count == 1
