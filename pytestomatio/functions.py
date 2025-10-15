from pytestomatio.services.meta_storage import meta_storage
from pytestomatio.services.link_storage import link_storage
from pytestomatio.utils.helper import get_current_test_id


def add_meta(data: dict):
    """
    Add metadata to the reported test
    :param data: metadata to add
    """
    test_id = get_current_test_id()
    if not test_id:
        return
    meta_storage.put(test_id, data)


def add_label(key: str, value: str = None):
    """
    Add a single label to the reported test
    :param key: label key (e.g. 'severity', 'feature', or just 'smoke' for labels without values)
    :param value: optional label value (e.g. 'high', 'login')
    """
    test_id = get_current_test_id()
    if not test_id:
        return
    data = f'{key}:{value}' if value else key
    link_storage.put(test_id, {'label': data})


def link_jira(*args: str):
    """
    Links JIRA issue IDs to the test report
    :param args: JIRA issue IDs to link
    """
    test_id = get_current_test_id()
    if not test_id:
        return
    for jira_id in args:
        link_storage.put(test_id, {'jira': jira_id})


def link_test(*args: str):
    """
    Links test IDs to the current test in the report
    :param args: test IDs to link
    """
    test_id = get_current_test_id()
    if not test_id:
        return
    for test in args:
        link_storage.put(test_id, {'test': test})
