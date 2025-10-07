import pytest
from unittest.mock import Mock, patch

from pytestomatio.utils.logging import _TEST_LOGS, add_log, get_test_logs, clear_test_logs


@pytest.fixture(autouse=True)
def clean_logs():
    _TEST_LOGS.clear()
    yield
    _TEST_LOGS.clear()


class TestAddLog:
    """Tests for add_log function"""

    def test_add_log_with_current_item(self):
        """Test log added when pytest._current_item is set"""
        mock_item = Mock()
        mock_item.nodeid = 'test_module.py::test_function'

        with patch.object(pytest, '_current_item', mock_item, create=True):
            add_log('Test message')

        assert 'test_module.py::test_function' in _TEST_LOGS
        assert _TEST_LOGS['test_module.py::test_function'] == ['[INFO] Test message']

    def test_add_log_custom_level(self):
        """Test log add with custom level"""
        mock_item = Mock()
        mock_item.nodeid = 'test_id'

        with patch.object(pytest, '_current_item', mock_item, create=True):
            add_log('Error message', 'ERROR')

        assert _TEST_LOGS['test_id'] == ['[ERROR] Error message']

    def test_add_multiple_logs(self):
        """Test attach multiple logs to one test"""
        mock_item = Mock()
        mock_item.nodeid = 'test_id'

        with patch.object(pytest, '_current_item', mock_item, create=True):
            add_log('First message', 'INFO')
            add_log('Second message', 'WARNING')
            add_log('Third message', 'ERROR')

        assert len(_TEST_LOGS['test_id']) == 3
        assert _TEST_LOGS['test_id'] == [
            '[INFO] First message',
            '[WARNING] Second message',
            '[ERROR] Third message'
        ]

    def test_add_log_to_different_tests(self):
        """Test log attach to different tests"""
        mock_item1 = Mock()
        mock_item1.nodeid = 'test_1'

        with patch.object(pytest, '_current_item', mock_item1, create=True):
            add_log('Message for test 1')

        mock_item2 = Mock()
        mock_item2.nodeid = 'test_2'

        with patch.object(pytest, '_current_item', mock_item2, create=True):
            add_log('Message for test 2')

        assert len(_TEST_LOGS) == 2
        assert _TEST_LOGS['test_1'] == ['[INFO] Message for test 1']
        assert _TEST_LOGS['test_2'] == ['[INFO] Message for test 2']


class TestGetTestLogs:
    """Tests for get_test_logs function"""

    def test_get_logs_as_list(self):
        """Test logs can be received as list"""
        _TEST_LOGS['test_id'] = ['[INFO] Log 1', '[ERROR] Log 2']

        logs = get_test_logs('test_id')

        assert isinstance(logs, list)
        assert logs == ['[INFO] Log 1', '[ERROR] Log 2']

    def test_get_logs_as_string(self):
        """Test logs can be received as string"""
        _TEST_LOGS['test_id'] = ['[INFO] Log 1', '[ERROR] Log 2']

        logs = get_test_logs('test_id', as_string=True)

        assert isinstance(logs, str)
        assert logs == '[INFO] Log 1\n[ERROR] Log 2'

    def test_get_logs_single_log(self):
        """Test log can be received"""
        _TEST_LOGS['test_id'] = ['[INFO] Single log']

        logs = get_test_logs('test_id', as_string=True)

        assert logs == '[INFO] Single log'


class TestClearTestLogs:
    """Tests for clear_test_logs function"""

    def test_clear_existing_logs(self):
        """Test clearing existing logs"""
        _TEST_LOGS['test_id'] = ['[INFO] Log 1', '[ERROR] Log 2']

        clear_test_logs('test_id')

        assert 'test_id' not in _TEST_LOGS

    def test_clear_nonexistent_logs(self):
        """Test clearing nonexistent logs not raise error"""
        clear_test_logs('nonexistent_test')

        assert 'nonexistent_test' not in _TEST_LOGS

    def test_clear_does_not_affect_other_tests(self):
        """Test clearing does not affect other tests"""
        _TEST_LOGS['test_1'] = ['[INFO] Log 1']
        _TEST_LOGS['test_2'] = ['[INFO] Log 2']

        clear_test_logs('test_1')

        assert 'test_1' not in _TEST_LOGS
        assert 'test_2' in _TEST_LOGS
        assert _TEST_LOGS['test_2'] == ['[INFO] Log 2']
