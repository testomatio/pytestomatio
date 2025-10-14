from pytestomatio.services.meta_storage import meta_storage
from pytestomatio.utils.helper import get_current_test_id


def add_meta(data: dict):
    test_id = get_current_test_id()
    if not test_id:
        return
    meta_storage.put(test_id, data)
