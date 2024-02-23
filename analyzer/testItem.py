import uuid
import json
from pytest import Item
import inspect

MARKER = 'testomatio'
# TODO: identify test is parameterized or not
class TestItem:
    def __init__(self, item: Item):
        self.uid = uuid.uuid4()
        self.id: str = TestItem.get_test_id(item)
        self.title = _get_pytest_title(item.name)
        self.sync_title = _get_sync_test_title(item)
        self.resync_title = _get_resync_test_title(item)
        self.exec_title = _get_execution_test_title(item)
        self.file_name = item.path.name
        self.abs_path = str(item.path)
        self.file_path = item.location[0]
        self.module = item.module.__name__
        # self.source_code: str = "TBD"
        # straitforward way, does not work with test packages
        self.source_code = inspect.getsource(item.function)
        self.class_name = item.cls.__name__ if item.cls else None
        self.artifacts = item.stash.get("artifact_urls", [])
    
    def to_dict(self) -> dict:
        result = dict()
        result['uid'] = str(self.uid)
        result['id'] = self.id
        result['title'] = self.title
        result['fileName'] = self.file_name
        result['absolutePath'] = self.abs_path
        result['filePath'] = self.file_path
        result['module'] = self.module
        result['className'] = self.class_name
        result['sourceCode'] = self.source_code
        result['artifacts'] = self.artifacts
        return result

    def json(self) -> str:
        return json.dumps(self.to_dict(), indent=4)

    @staticmethod
    def get_test_id(item: Item) -> str | None:
        for marker in item.iter_markers(MARKER):
            if marker.args:
                return marker.args[0]

    def __str__(self) -> str:
        return f'TestItem: {self.id} - {self.title} - {self.file_name}'

    def __repr__(self):
        return f'TestItem: {self.id} - {self.title} - {self.file_name}'

def _get_pytest_title(name: str) -> str:
    point = name.find('[')
    if point > -1:
        return name[0:point]
    return name

# Testomatio resolves test id on BE by parsing test name to find test id
def _get_sync_test_title(item: Item) -> str:
    test_name = item.name
    parameter_at = item.name.find('[')
    if parameter_at > -1:
        test_name = test_name[0:parameter_at] + " ${" + item.get_closest_marker('parametrize').args[0] + "}"
    test_id = TestItem.get_test_id(item)
    test_name = pytest_title_to_testomatio_title(test_name)
    # Test id is present on already synced tests
    if (test_id):
        test_name = f'{test_name} {test_id}'
    # New test don't have testomatio test id.
    return test_name

def _get_execution_test_title(item: Item) -> str:
    test_name = item.name
    parameter_at = item.name.find('[')
    if parameter_at > -1:
        test_name = test_name[0:parameter_at] + " " + test_name[parameter_at:]
    test_id = TestItem.get_test_id(item)
    # Test id is present on already synced tests
    if (test_id):
        test_name = f'{test_name} {test_id}'
    # New test don't have testomatio test id.
    return pytest_title_to_testomatio_title(test_name)

def pytest_title_to_testomatio_title(test_name: str) -> str:
    return test_name.lower().replace('_', ' ').replace("test", "", 1).strip().capitalize()

def _get_resync_test_title(name) -> str:
    name = _get_sync_test_title(name)
    tag_at = name.find("@T")
    if tag_at > 0:
        return name[0:tag_at].strip()
    else:
        return name
