import pytest
import os

from unittest.mock import Mock, patch, call, mock_open

from pytestomatio import main

testomatio = 'testomatio'
testomatio_url = 'https://app.testomat.io'
testomation_custom_url = 'https://custom.testomat.io'
testomatio_api_key = 'test_token'

pytest_plugins = ["pytester"]


@pytest.mark.smoke
class TestPytestAddOption:
    """Tests for pytest_addoption hook"""

    def test_pytest_addoption_calls_parser_options(self):
        """Test pytest_addoption calls parser_options"""
        mock_parser = Mock()

        main.pytest_addoption(mock_parser)
        assert mock_parser.method_calls


@pytest.mark.smoke
class TestPytestCollection:
    """Tests for pytest_collection hook"""

    def test_pytest_collection_stores_original_items(self):
        """Test stores original collected items"""
        mock_session = Mock()

        main.pytest_collection(mock_session)
        store_attribute_name = '_pytestomatio_original_collected_items'

        assert hasattr(mock_session, store_attribute_name)
        assert mock_session._pytestomatio_original_collected_items == []


@pytest.mark.smoke
class TestPytestConfigure:
    """Tests for pytest_configure hook"""

    def teardown_method(self):
        """Clear pytest namespace after test"""
        if hasattr(pytest, 'testomatio'):
            delattr(pytest, 'testomatio')

    @pytest.fixture
    def mock_config(self):
        """Configuration mock"""
        config = Mock(spec=['addinivalue_line', 'getini', 'getoption', 'pluginmanager'])
        config.getoption = Mock(return_value=None)
        return config

    @patch('pytestomatio.main.validations.validate_option')
    def test_configure_adds_testomatio_marker(self, mock_validate, mock_config):
        """Test configuration add testomatio marker"""
        mock_validate.return_value = 'debug'
        main.pytest_configure(mock_config)

        mock_config.addinivalue_line.assert_called_with(
            "markers",
            "testomatio(arg): built in marker to connect test case with testomat.io by unique id"
        )

    @patch('pytestomatio.main.validations.validate_option')
    def test_configure_debug_mode_early_return(self, mock_validate, mock_config):
        """Test early exit in debug mode"""
        mock_validate.return_value = 'debug'

        main.pytest_configure(mock_config)

        assert mock_config.addinivalue_line.call_count == 1
        assert not hasattr(pytest, 'testomatio') or pytest.testomatio is None

    @patch('pytestomatio.main.validations.validate_option')
    @patch('pytestomatio.main.Connector')
    @patch.dict(os.environ, {'TESTOMATIO': testomatio_api_key, 'TESTOMATIO_URL': testomation_custom_url})
    def test_configure_custom_url_from_env(self, mock_connector, mock_validate, mock_config):
        """Test get custom URL from environment"""
        mock_validate.return_value = 'sync'

        main.pytest_configure(mock_config)

        mock_connector.assert_called_once_with(testomation_custom_url, testomatio_api_key)

    @patch('pytestomatio.main.validations.validate_option')
    @patch('pytestomatio.main.Connector')
    @patch.dict(os.environ, {'TESTOMATIO': testomatio_api_key})
    def test_configure_custom_url_from_ini(self, mock_connector, mock_validate, mock_config):
        """Test get custom URL from ini file"""
        mock_validate.return_value = 'sync'
        mock_config.getini.return_value = testomation_custom_url

        main.pytest_configure(mock_config)

        mock_connector.assert_called_once_with(testomation_custom_url, testomatio_api_key)

    @patch('pytestomatio.main.validations.validate_option')
    @patch('pytestomatio.main.Testomatio')
    def test_configure_test_run_env(self, mock_testomatio, mock_validate, mock_config):
        """Test configuration test run environment"""
        mock_validate.return_value = 'sync'
        env = 'linux,chrome'
        mock_config.getoption.side_effect = lambda x: env if x == 'testRunEnv' else None

        mock_testomatio_instance = Mock()
        mock_testomatio.return_value = mock_testomatio_instance

        main.pytest_configure(mock_config)

        mock_testomatio_instance.test_run_config.set_env.assert_called_once_with(env)

    @patch('pytestomatio.main.validations.validate_option')
    @patch('pytestomatio.main.Testomatio')
    @patch('pytestomatio.main.Connector')
    @patch.dict(os.environ, {'TESTOMATIO': testomatio_api_key})
    def test_configure_report_mode_creates_test_run(self, mock_connector, mock_testomatio, mock_validate, mock_config):
        """Тest test run created in report mode"""
        mock_validate.return_value = 'report'
        mock_config.getoption.side_effect = lambda x: 'report' if x == 'testomatio' else None

        assert not hasattr(mock_config, 'workerinput')

        mock_testomatio_instance = Mock()
        mock_testomatio.return_value = mock_testomatio_instance
        mock_testomatio_instance.test_run_config.test_run_id = None
        mock_testomatio_instance.test_run_config.to_dict.return_value = {'title': 'Test Run'}

        mock_connector_instance = Mock()
        mock_connector.return_value = mock_connector_instance
        mock_connector_instance.create_test_run.return_value = {'uid': 'run_12345'}

        main.pytest_configure(mock_config)

        mock_connector_instance.create_test_run.assert_called_once_with(title='Test Run')
        mock_testomatio_instance.test_run_config.save_run_id.assert_called_once_with('run_12345')


class TestPytestCollectionModifyItems:
    """Tests for pytest_collection_modifyitems hook"""

    def teardown_method(self):
        """Clear pytest namespace after test"""
        if hasattr(pytest, 'testomatio'):
            delattr(pytest, 'testomatio')

    @pytest.fixture
    def mock_session(self):
        session = Mock()
        session._pytestomatio_original_collected_items = []
        return session

    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.getoption.return_value = None
        return config

    def test_early_return_when_no_testomatio_option(self, mock_session, mock_config, multiple_test_items):
        """Test early exit when no testomatio option"""
        items = multiple_test_items.copy()
        main.pytest_collection_modifyitems(mock_session, mock_config, items)
        assert len(items) == len(multiple_test_items)

    @patch('pytestomatio.main.pytest.exit')
    def test_sync_mode(self, mock_exit, mock_session, mock_config, multiple_test_items):
        """Test sync mode"""
        mock_config.getoption.side_effect = lambda x: {
            'testomatio': 'sync',
            'no_empty': False,
            'no_detach': False,
            'keep_structure': False,
            'create': False,
            'directory': None
        }.get(x)
        items = multiple_test_items.copy()

        pytest.testomatio = Mock()
        pytest.testomatio.connector = Mock()
        pytest.testomatio.connector.get_tests.return_value = []

        with patch('pytestomatio.main.add_and_enrich_tests') as mock_add_enrich:
            main.pytest_collection_modifyitems(mock_session, mock_config, items)

            assert pytest.testomatio.connector.load_tests.call_count == 1
            passed_meta = pytest.testomatio.connector.load_tests.call_args[0][0]
            assert passed_meta[0].title == items[0].name

            assert mock_add_enrich.call_count == 1
            mock_exit.assert_called_once_with('Sync completed without test execution')

    @patch('pytestomatio.main.update_tests')
    @patch('pytestomatio.main.pytest.exit')
    def test_remove_mode(self, mock_exit, mock_update_tests, mock_session, mock_config, single_test_item,
                         multiple_test_items):
        """Test remove mode"""
        mock_config.getoption.side_effect = lambda x: 'remove' if x == 'testomatio' else None

        items = single_test_item.copy() + multiple_test_items.copy()

        main.pytest_collection_modifyitems(mock_session, mock_config, items)

        assert mock_update_tests.call_count == 2
        mock_exit.assert_called_once_with('Sync completed without test execution')

    @patch('pytestomatio.main.read_env_s3_keys')
    def test_report_mode_without_s3(self, mock_read_s3, mock_session, mock_config, multiple_test_items):
        """Test report mode without S3"""
        mock_config.getoption.side_effect = lambda x: 'report' if x == 'testomatio' else None
        mock_read_s3.return_value = ('region', '', 'secret_key', 'endpoint', 'bucket', 'path')
        items = multiple_test_items.copy()
        run_id = 'E534ere'

        pytest.testomatio = Mock()
        pytest.testomatio.test_run_config = Mock()
        pytest.testomatio.test_run_config.get_run_id.return_value = run_id
        pytest.testomatio.test_run_config.to_dict.return_value = {'id': run_id}
        pytest.testomatio.connector = Mock()
        pytest.testomatio.connector.update_test_run.return_value = {'rid': 1234}

        with patch('pytestomatio.main.S3Connector') as mock_s3_connector:
            main.pytest_collection_modifyitems(mock_session, mock_config, items)

            assert pytest.testomatio.test_run_config.get_run_id.called
            assert pytest.testomatio.connector.update_test_run.called

            args = pytest.testomatio.connector.update_test_run.call_args[-1]
            assert 'id' in args
            assert args.get('id') == run_id
            assert not mock_s3_connector.called
            assert not pytest.testomatio.s3_connector.login.called

    @patch('pytestomatio.main.read_env_s3_keys')
    def test_report_mode_with_s3(self, mock_read_s3, mock_session, mock_config, multiple_test_items):
        """Test report mode with S3"""
        mock_config.getoption.side_effect = lambda x: 'report' if x == 'testomatio' else None
        items = multiple_test_items.copy()
        run_id = 'E534ere'
        mock_read_s3.return_value = ('region', 'access_key', 'secret_key', 'endpoint', 'bucket', 'path')

        pytest.testomatio = Mock()
        pytest.testomatio.test_run_config = Mock()
        pytest.testomatio.test_run_config.get_run_id.return_value = run_id
        pytest.testomatio.test_run_config.to_dict.return_value = {'id': run_id}
        pytest.testomatio.connector = Mock()
        pytest.testomatio.connector.update_test_run.return_value = {'rid': 1234}

        with patch('pytestomatio.main.S3Connector') as mock_s3_connector:
            main.pytest_collection_modifyitems(mock_session, mock_config, items)

            assert pytest.testomatio.test_run_config.get_run_id.called
            assert pytest.testomatio.connector.update_test_run.called

            args = pytest.testomatio.connector.update_test_run.call_args[-1]
            assert 'id' in args
            assert args.get('id') == run_id

            mock_s3_connector.assert_called_once_with('region', 'access_key', 'secret_key', 'endpoint', 'bucket', 'path')
            assert pytest.testomatio.s3_connector.login.call_count == 1

    @patch('builtins.open', new_callable=mock_open)
    @patch('pytestomatio.main.json.dumps')
    @patch('pytestomatio.main.pytest.exit')
    def test_debug_mode(self, mock_exit, mock_json_dumps, mock_file,
                        mock_session, mock_config, multiple_test_items):
        """Test debug mode"""
        mock_config.getoption.side_effect = lambda x: 'debug' if x == 'testomatio' else None
        items = multiple_test_items.copy()

        main.pytest_collection_modifyitems(mock_session, mock_config, items)

        mock_file.assert_called_once_with('metadata.json', 'w')
        assert mock_json_dumps.call_count == 1
        mock_exit.assert_called_once_with('Debug file created. Exiting...')

    def test_unknown_option_raises_exception(self, mock_session, mock_config, multiple_test_items):
        """Test unknow option raises exception"""
        items = multiple_test_items.copy()
        mock_config.getoption.side_effect = lambda x: 'unknown_option' if x == 'testomatio' else None

        with patch('pytestomatio.main.collect_tests') as mock_collect_tests:
            mock_collect_tests.return_value = ([], [], [])

            with pytest.raises(Exception, match='Unknown pytestomatio parameter'):
                main.pytest_collection_modifyitems(mock_session, mock_config, items)


@pytest.mark.smoke
class TestPytestRuntestMakereport:
    """Tests for pytest_runtest_makereport hook"""

    @pytest.fixture
    def mock_item(self):
        item = Mock()
        item.config.getoption.return_value = 'report'
        return item

    @pytest.fixture
    def mock_call(self):
        call = Mock()
        return call

    def setup_method(self):
        """Clear pytest namespace"""
        if hasattr(pytest, 'testomatio_config_option'):
            delattr(pytest, 'testomatio_config_option')
        if hasattr(pytest, 'testomatio'):
            delattr(pytest, 'testomatio')

    def test_early_return_no_testomatio_option(self, mock_item, mock_call):
        """Test early return if no testomatio option"""
        mock_item.config.getoption.return_value = None

        result = main.pytest_runtest_makereport(mock_item, mock_call)

        assert result is None
        mock_item.config.getoption.assert_called_once_with('testomatio')

    def test_early_return_wrong_option(self, mock_item, mock_call):
        """Test early exit if option is not report"""
        mock_item.config.getoption.return_value = 'sync'

        result = main.pytest_runtest_makereport(mock_item, mock_call)

        assert result is None

    def test_early_return_no_run_id(self, mock_item, mock_call):
        """Test early exit if no run_id"""

        pytest.testomatio = Mock()
        pytest.testomatio.test_run_config = Mock()
        pytest.testomatio.test_run_config.test_run_id = None

        result = main.pytest_runtest_makereport(mock_item, mock_call)

        assert result is None

    def test_creates_test_request_structure(self, mock_call, single_test_item):
        """Тест що функція створює правильну структуру запиту"""
        item = single_test_item.copy()[0]
        item.config.option.testomatio = 'report'

        mock_call.duration = 1.5
        mock_call.when = 'call'
        mock_call.excinfo = None

        pytest.testomatio = Mock()
        pytest.testomatio.test_run_config = Mock()
        pytest.testomatio.test_run_config.test_run_id = 'run_123'
        pytest.testomatio.test_run_config.status_request = {}

        main.pytest_runtest_makereport(item, mock_call)

        assert item.nodeid in pytest.testomatio.test_run_config.status_request
        request = pytest.testomatio.test_run_config.status_request[item.nodeid]

        expected_keys = [
            'status', 'title', 'run_time', 'suite_title', 'suite_id',
            'test_id', 'message', 'stack', 'example', 'artifacts', 'steps', 'code'
        ]
        for key in expected_keys:
            assert key in request

        assert request['status'] == 'passed'
        assert request['title'] == 'Addition'
        assert request['run_time'] == 1.5
        assert request['suite_title'] == item.path.name
        assert request['test_id'] == '12345678'

    def test_processing_skipped_test(self, mock_call, single_test_item):
        """Test skipped test reported"""
        item = single_test_item.copy()[0]
        item.config.option.testomatio = 'report'

        mock_call.duration = 1.5
        mock_call.when = 'call'
        exc_info = Mock()
        exc_info.typename = 'Skipped'
        mock_call.excinfo = exc_info

        pytest.testomatio = Mock()
        pytest.testomatio.test_run_config = Mock()
        pytest.testomatio.test_run_config.test_run_id = 'run_123'
        pytest.testomatio.test_run_config.exclude_skipped = False
        pytest.testomatio.test_run_config.status_request = {}

        main.pytest_runtest_makereport(item, mock_call)

        assert item.nodeid in pytest.testomatio.test_run_config.status_request
        request = pytest.testomatio.test_run_config.status_request[item.nodeid]

        expected_keys = [
            'status', 'title', 'run_time', 'suite_title', 'suite_id',
            'test_id', 'message', 'stack', 'example', 'artifacts', 'steps', 'code'
        ]
        for key in expected_keys:
            assert key in request

        assert request['status'] == 'skipped'
        assert request['title'] == 'Addition'
        assert request['run_time'] == 1.5
        assert request['suite_title'] == item.path.name
        assert request['test_id'] == '12345678'

        mock_call.when = 'teardown'
        main.pytest_runtest_makereport(item, mock_call)

        assert item.nodeid in pytest.testomatio.test_run_config.status_request
        request = pytest.testomatio.test_run_config.status_request[item.nodeid]

        expected_keys = [
            'status', 'title', 'run_time', 'suite_title', 'suite_id',
            'test_id', 'message', 'stack', 'example', 'artifacts', 'steps', 'code'
        ]
        for key in expected_keys:
            assert key in request

        assert request['status'] == 'skipped'
        assert request['title'] == 'Addition'
        assert request['run_time'] == 1.5
        assert request['suite_title'] == item.path.name
        assert request['test_id'] == '12345678'

    def test_exclude_skipped_test_if_option_enabled(self, mock_call, single_test_item):
        """Test skipped test excluded from report if TESTOMATIO_EXCLUDE_SKIPPED option is enabled"""
        item = single_test_item.copy()[0]
        item.config.option.testomatio = 'report'

        mock_call.duration = 1.5
        mock_call.when = 'call'
        exc_info = Mock()
        exc_info.typename = 'Skipped'
        mock_call.excinfo = exc_info

        pytest.testomatio = Mock()
        pytest.testomatio.test_run_config = Mock()
        pytest.testomatio.test_run_config.test_run_id = 'run_123'
        pytest.testomatio.test_run_config.exclude_skipped = True
        pytest.testomatio.test_run_config.status_request = {}

        main.pytest_runtest_makereport(item, mock_call)

        assert item.nodeid in pytest.testomatio.test_run_config.status_request
        request = pytest.testomatio.test_run_config.status_request[item.nodeid]

        expected_keys = [
            'status', 'title', 'run_time', 'suite_title', 'suite_id',
            'test_id', 'message', 'stack', 'example', 'artifacts', 'steps', 'code'
        ]
        for key in expected_keys:
            assert key in request

        assert request['status'] == 'skipped'
        assert request['title'] == 'Addition'
        assert request['run_time'] == 1.5
        assert request['suite_title'] == item.path.name
        assert request['test_id'] == '12345678'

        mock_call.when = 'teardown'
        main.pytest_runtest_makereport(item, mock_call)

        assert item.nodeid not in pytest.testomatio.test_run_config.status_request
        assert pytest.testomatio.test_run_config.status_request == {}


@pytest.mark.smoke
class TestPytestUnconfigure:
    """Tests for pytest_unconfigure hook"""

    def teardown_method(self):
        if hasattr(pytest, 'testomatio'):
            delattr(pytest, 'testomatio')

    def test_unconfigure_early_return_no_testomatio(self):
        """Test early exit if no pytest.testomatio"""
        mock_config = Mock()

        if hasattr(pytest, 'testomatio'):
            delattr(pytest, 'testomatio')

        assert not hasattr(pytest, 'testomatio')

        result = main.pytest_unconfigure(mock_config)
        assert result is None

    @patch('pytestomatio.main.time.sleep')
    def test_unconfigure_main_process_cleanup(self, mock_sleep):
        """Test cleanup in main process"""
        mock_config = Mock(spec=['addinivalue_line', 'getini', 'getoption', 'pluginmanager'])
        assert not hasattr(mock_config, 'workerinput')

        pytest.testomatio = Mock()
        pytest.testomatio.test_run_config = Mock()
        pytest.testomatio.test_run_config.test_run_id = 'test_run_123'
        pytest.testomatio.connector = Mock()

        main.pytest_unconfigure(mock_config)

        mock_sleep.assert_called_once_with(1)
        pytest.testomatio.connector.finish_test_run.assert_called_once_with('test_run_123', True)
        assert pytest.testomatio.test_run_config.clear_run_id.call_count == 1

    def test_unconfigure_xdist_worker_cleanup(self):
        """Test cleanup in xdist worker process"""
        mock_config = Mock()
        mock_config.workerinput = Mock()

        pytest.testomatio = Mock()
        pytest.testomatio.test_run_config = Mock()
        pytest.testomatio.test_run_config.test_run_id = 'worker_run_456'
        pytest.testomatio.connector = Mock()

        main.pytest_unconfigure(mock_config)

        pytest.testomatio.connector.finish_test_run.assert_called_once_with('worker_run_456', False)
        pytest.testomatio.test_run_config.clear_run_id.assert_not_called()


@pytest.mark.smoke
class TestPytestRuntestLogfinish:
    """Tests for pytest_runtest_logfinish hook"""

    def setup_method(self):
        if hasattr(pytest, 'testomatio_config_option'):
            delattr(pytest, 'testomatio_config_option')
        if hasattr(pytest, 'testomatio'):
            delattr(pytest, 'testomatio')

    def test_logfinish_early_return_no_config_option(self):
        """Test early exit if no testomatio_config_option"""
        result = main.pytest_runtest_logfinish('test_nodeid', ('file.py', 1, 'test'))

        assert result is None

    def test_logfinish_early_return_wrong_config_option(self):
        """Test early exit if wrong config option"""
        pytest.testomatio_config_option = 'sync'

        result = main.pytest_runtest_logfinish('test_nodeid', ('file.py', 1, 'test'))
        assert result is None

    def test_logfinish_early_return_none_config_option(self):
        """Test early exit if config option is None"""
        pytest.testomatio_config_option = None

        result = main.pytest_runtest_logfinish('test_nodeid', ('file.py', 1, 'test'))
        assert result is None

    def test_logfinish_early_return_no_run_id(self):
        """Test early exit when no test_run_id"""
        pytest.testomatio_config_option = 'report'
        pytest.testomatio = Mock()
        pytest.testomatio.test_run_config = Mock()
        pytest.testomatio.test_run_config.test_run_id = None

        result = main.pytest_runtest_logfinish('test_nodeid', ('file.py', 1, 'test'))
        assert result is None

    def test_logfinish_processes_status_requests_with_status(self):
        """Test processes tests with status"""
        pytest.testomatio_config_option = 'report'
        pytest.testomatio = Mock()
        pytest.testomatio.test_run_config = Mock()
        pytest.testomatio.test_run_config.test_run_id = 'run_123'
        pytest.testomatio.connector = Mock()

        status_requests = {
            'test1::nodeid': {
                'status': 'passed',
                'title': 'Test One',
                'run_time': 1.5
            },
            'test2::nodeid': {
                'status': 'failed',
                'title': 'Test Two',
                'message': 'Test failed',
                'run_time': 2.0
            },
            'test3::nodeid': {
                'status': None,
                'title': 'Test Three'
            }
        }
        pytest.testomatio.test_run_config.status_request = status_requests

        main.pytest_runtest_logfinish('current_nodeid', ('file.py', 1, 'test'))

        expected_calls = [
            call(run_id='run_123', status='passed', title='Test One', run_time=1.5),
            call(run_id='run_123', status='failed', title='Test Two',
                 message='Test failed', run_time=2.0)
        ]
        pytest.testomatio.connector.update_test_status.assert_has_calls(
            expected_calls, any_order=True
        )

        assert pytest.testomatio.connector.update_test_status.call_count == 2

    def test_logfinish_clears_status_request_after_processing(self):
        """Тест status_request cleared after processing"""
        pytest.testomatio_config_option = 'report'
        pytest.testomatio = Mock()
        pytest.testomatio.test_run_config = Mock()
        pytest.testomatio.test_run_config.test_run_id = 'run_456'
        pytest.testomatio.connector = Mock()

        pytest.testomatio.test_run_config.status_request = {
            'test::nodeid': {'status': 'passed', 'title': 'Test'}
        }

        main.pytest_runtest_logfinish('nodeid', ('file.py', 1, 'test'))

        assert pytest.testomatio.test_run_config.status_request == {}

    def test_logfinish_empty_status_request(self):
        """Test with empty status_request"""
        pytest.testomatio_config_option = 'report'
        pytest.testomatio = Mock()
        pytest.testomatio.test_run_config = Mock()
        pytest.testomatio.test_run_config.test_run_id = 'run_789'
        pytest.testomatio.connector = Mock()
        pytest.testomatio.test_run_config.status_request = {}

        main.pytest_runtest_logfinish('nodeid', ('file.py', 1, 'test'))

        pytest.testomatio.connector.update_test_status.assert_not_called()

        assert pytest.testomatio.test_run_config.status_request == {}
