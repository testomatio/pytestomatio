from re import sub
from typing import Iterable
import uuid
import json
from pytest import Item
import inspect

MARKER = 'testomatio'
class TestItem:
    def __init__(self, item: Item):
        self.uid = uuid.uuid4()
        self.id: str = TestItem.get_test_id(item)
        self.title = self._get_pytest_title(item.name)
        self.sync_title = self._get_sync_test_title(item)
        self.resync_title = self._get_resync_test_title(item)
        self.exec_title = self._get_execution_test_title(item)
        self.parameters = self._get_test_parameter_key(item)
        self.file_name = item.path.name
        self.abs_path = str(item.path)
        self.file_path = item.location[0]
        self.module = item.module.__name__
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
        return f'TestItem: {self.id} - {self.title} - {self.file_path}'

    def __repr__(self):
        return f'TestItem: {self.id} - {self.title} - {self.file_path}'

    def _get_pytest_title(self, name: str) -> str:
        point = name.find('[')
        if point > -1:
            return name[0:point]
        return name

    # Testomatio resolves test id on BE by parsing test name to find test id
    def _get_sync_test_title(self, item: Item) -> str:
        test_name = self.pytest_title_to_testomatio_title(item.name)
        test_name = self._resolve_parameter_key_in_test_name(item, test_name)
        # Test id is present on already synced tests
        # New test don't have testomatio test id.
        test_id = TestItem.get_test_id(item)
        if (test_id):
            test_name = f'{test_name} {test_id}'
        # ex. "User adds item to cart"
        # ex. "User adds item to cart @T1234"
        # ex. "User adds ${item} to cart @T1234"
        # ex. "User adds ${variation} ${item} to cart @T1234"
        return test_name

    #  Fix such example @pytest.mark.parametrize("version", "1.0.0"), ref. https://github.com/testomatio/check-tests/issues/147
    #  that doesn't parse value correctly
    def _get_execution_test_title(self, item: Item) -> str:
        test_name = self.pytest_title_to_testomatio_title(item.name)
        test_name = self._resolve_parameter_value_in_test_name(item, test_name)
        # ex. "User adds item to cart"
        # ex. "User adds item to cart @T1234"
        # ex. "User adds phone to cart @T1234"
        # ex. "User adds green phone to cart @T1234"
        return test_name

    def pytest_title_to_testomatio_title(self, test_name: str) -> str:
        return test_name.lower().replace('_', ' ').replace("test", "", 1).strip().capitalize()

    def _get_resync_test_title(self, name: str) -> str:
        name = self._get_sync_test_title(name)
        tag_at = name.find("@T")
        if tag_at > 0:
            return name[0:tag_at].strip()
        else:
            return name

    def _get_test_parameter_key(self, item: Item) -> bool:
        params = []
        for mark in item.iter_markers('parametrize'):
            is_list = mark.args[0].find(',') > -1
            if is_list:
                params.extend([p.strip() for p in mark.args[0].split(',')])
            else:
                params.append(mark.args[0])
        return params
    
    def _resolve_parameter_key_in_test_name(self, item: Item, test_name: str) -> str:
        test_params = self._get_test_parameter_key(item)
        if not test_params:
            return test_name
        # Remove parameters from test name
        parameter_at = test_name.find('[')
        if parameter_at > -1:
            test_name = test_name[0:parameter_at]
        # Add parameters to test name
        test_name = test_name + " " + " ".join([f"${{{param}}}" for param in test_params])
        return test_name
    
    def _resolve_parameter_value_in_test_name(self, item: Item, test_name: str) -> str:
        param_keys = self._get_test_parameter_key(item)
        sync_title = self._get_sync_test_title(item)
        if not param_keys:
            return test_name
        if not item.callspec:
            return test_name
        
        pattern = r'\$\{(.*?)\}'

        def repl(match):
            key = match.group(1)
            
            value = item.callspec.params.get(key, '')
            if type(value) is bytes:
                string_value = value.decode('utf-8')
            elif isinstance(value, (str, int, float, bool)):
                string_value = str(value)
            else:
                string_value = 'Unsupported type'
            # TODO: handle "value with space" on testomatio BE https://github.com/testomatio/check-tests/issues/147
            return sub(r"[\.\s]", "_", string_value) # Temporary fix for spaces in parameter values

        test_name = sub(pattern, repl, sync_title)
        return test_name