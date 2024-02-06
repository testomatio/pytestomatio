import uuid
import json
from pytest import Item

MARKER = 'testomatio'


class TestItem:
    def __init__(self, item: Item):
        self.uid = uuid.uuid4()
        self.id: str = TestItem.get_test_id(item)
        self.user_title = _prettify_test_name(item.name)
        self.title = _clear_param_brackets(item.name)
        self.sync_title = _get_sync_title(item)
        self.file_name = item.path.name
        self.abs_path = str(item.path)
        self.file_path = item.location[0]
        self.module = item.module.__name__
        self.source_code: str = None
        # straitforward way, does not work with test packages
        # self.source_code = getsource(item.function)
        self.class_name = item.cls.__name__ if item.cls else None
        self.artifacts = item.testomatio.get('artifacts', []) if hasattr(item, 'testomatio') else []
    
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


def _clear_param_brackets(name: str) -> str:
    point = name.find('[')
    if point > -1:
        return name[0:point]
    return name

# Testomatio resolves test id on BE by parsing test name to find test id
def _get_sync_title(item: Item) -> str:
    clean_name = _clear_param_brackets(item.name)
    test_id = TestItem.get_test_id(item)
    # Test id is present on already synced tests
    if (test_id):
        return f'{clean_name} {test_id}'
    # New test don't have testomatio test id.
    return clean_name


def _prettify_test_name(name: str) -> str:
    name = _clear_param_brackets(name)
    return name.lower().replace('_', ' ').lstrip('test').strip().capitalize()
