import pytest
from typing import List

_TEST_LOGS = {}


def add_log(message: str, level: str = 'INFO'):
    """
    Attach log to the test
    :param message: message text
    :param level: log level
    """
    if hasattr(pytest, '_current_item'):
        test_id = pytest._current_item.nodeid
    else:
        test_id = 'unknown'

    if test_id not in _TEST_LOGS:
        _TEST_LOGS[test_id] = []
    _TEST_LOGS[test_id].append(f'[{level.upper()}] {message}')


def get_test_logs(test_id: str, as_string=False) -> List[dict] or str:
    """Receive logs attached to given test"""
    logs = _TEST_LOGS.get(test_id, [])
    if as_string:
        logs = '\n'.join(logs)
    return logs


def clear_test_logs(test_id: str):
    """Clear logs for given test"""
    _TEST_LOGS.pop(test_id, None)


