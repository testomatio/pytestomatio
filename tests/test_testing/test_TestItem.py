import pytest
import uuid
import json
from unittest.mock import Mock, patch
from pytest import Item

from pytestomatio.testing.testItem import TestItem


class TestTestItem:
    """Tests for TestItem"""

    @pytest.fixture
    def mock_item(self):
        """Mock pytest Item"""
        item = Mock(spec=Item)
        item.name = "test_example"
        item.path = Mock()
        item.path.name = "test_file.py"
        item.location = ("test_file.py", 10, "test_example")
        item.module = Mock()
        item.module.__name__ = "test_module"
        item.function = Mock()
        item.cls = None
        item.stash = Mock()
        item.stash.get.return_value = []
        item.iter_markers.return_value = iter([])
        return item

    @pytest.fixture
    def mock_item_with_marker(self, mock_item):
        """Mock Item with testomatio marker"""
        marker = Mock()
        marker.args = ["@T12345678"]
        mock_item.iter_markers.return_value = iter([marker])
        return mock_item

    @patch('inspect.getsource')
    def test_init_basic(self, mock_getsource, mock_item):
        """Test basic init TestItem"""
        mock_getsource.return_value = "def test_example(): pass"

        test_item = TestItem(mock_item)

        assert isinstance(test_item.uid, uuid.UUID)
        assert test_item.id is None
        assert test_item.title == "test_example"
        assert test_item.file_name == "test_file.py"
        assert test_item.module == "test_module"
        assert test_item.source_code == "def test_example(): pass"
        assert test_item.class_name is None
        assert test_item.artifacts == []
        assert test_item.type == 'regular'

    @patch('inspect.getsource')
    def test_init_with_marker(self, mock_getsource, mock_item_with_marker):
        """Test init with testomatio marker"""
        mock_getsource.return_value = "def test_example(): pass"

        test_item = TestItem(mock_item_with_marker)

        assert test_item.id == "@T12345678"

    @patch('inspect.getsource')
    def test_init_with_class(self, mock_getsource, mock_item):
        """Test init with class name"""
        mock_getsource.return_value = "def test_method(self): pass"
        mock_item.cls = Mock()
        mock_item.cls.__name__ = "TestClass"

        test_item = TestItem(mock_item)

        assert test_item.class_name == "TestClass"

    @patch("inspect.getsource")
    def test_get_test_id_with_marker(self, mock_source, mock_item):
        """Test get_test_id with marker"""
        marker = Mock()
        marker.name = 'testomatio'
        marker.args = ["@T87654321"]
        mock_item.iter_markers.return_value = iter([marker])
        test_item = TestItem(mock_item)
        mock_item.iter_markers.return_value = iter([marker])
        result = test_item.get_test_id(mock_item)

        assert result == "@T87654321"
        assert result == test_item.id

    @patch("inspect.getsource")
    def test_get_test_id_with_other_markers(self, mock_source, mock_item):
        """Test get_test_id with other marker"""
        marker = Mock()
        marker.name = 'other'
        marker.args = ["@T87654321"]
        markers = [marker]
        mock_item.iter_markers.side_effect = lambda name=None: iter(
            [m for m in markers if name is None or m.name == name])
        test_item = TestItem(mock_item)
        result = test_item.get_test_id(mock_item)

        assert result is None
        assert test_item.id is None

    @patch("inspect.getsource")
    def test_get_test_id_without_marker(self, mock_source, mock_item):
        """Test get_test_id without marker"""
        mock_item.iter_markers.return_value = iter([])
        test_item = TestItem(mock_item)
        result = test_item.get_test_id(mock_item)

        assert result is None
        assert test_item.id is None

    @patch("inspect.getsource")
    def test_get_test_id_for_bdd_test(self, mock_source, mock_item):
        """Test get_test_id with correct marker for bdd test"""
        marker = Mock()
        marker.name = "T87654321"
        mock_item.iter_markers.return_value = iter([marker])
        mock_item.function.__scenario__ = True
        test_item = TestItem(mock_item)
        mock_item.iter_markers.return_value = iter([marker])
        result = test_item.get_test_id(mock_item)
        assert result == "@T87654321"
        assert test_item.id == result

    @patch("inspect.getsource")
    def test_get_test_id_for_bdd_test_with_other_marker(self, mock_source, mock_item):
        """Test get_test_id without correct marker for bdd test"""
        marker = Mock()
        marker.name = 'other_marker'
        marker.args = ["@T87654321"]
        mock_item.iter_markers.return_value = iter([marker])
        mock_item.function.__scenario__ = True
        test_item = TestItem(mock_item)
        result = test_item.get_test_id(mock_item)
        assert result is None
        assert test_item.id is None

    @patch("inspect.getsource")
    def test_get_test_id_for_bdd_test_without_marker(self, mock_source, mock_item):
        """Test get_test_id without marker for bdd test"""
        mock_item.iter_markers.return_value = iter([])
        mock_item.function.__scenario__ = True
        test_item = TestItem(mock_item)
        result = test_item.get_test_id(mock_item)

        assert result is None
        assert test_item.id is None

    def test_get_pytest_title_simple(self, mock_item):
        """Test _get_pytest_title without params"""
        test_item = TestItem.__new__(TestItem)

        result = test_item._get_pytest_title("test_simple")

        assert result == "test_simple"

    def test_get_pytest_title_with_parameters(self, mock_item):
        """Test _get_pytest_title with params"""
        test_item = TestItem.__new__(TestItem)

        result = test_item._get_pytest_title("test_param[value1-value2]")

        assert result == "test_param"

    def test_pytest_title_to_testomatio_title(self, mock_item):
        """Test convert pytest title in testomatio title"""
        test_item = TestItem.__new__(TestItem)

        assert test_item.pytest_title_to_testomatio_title("test_user_login") == "User login"
        assert test_item.pytest_title_to_testomatio_title("test_test_case") == "Test case"
        assert test_item.pytest_title_to_testomatio_title("user_logout") == "User logout"
        assert test_item.pytest_title_to_testomatio_title("TEST_API_CALL") == "Api call"

    def test_get_test_parameter_key_no_params(self, mock_item):
        """Test _get_test_parameter_key without params"""
        mock_item.iter_markers.return_value = iter([])
        test_item = TestItem.__new__(TestItem)

        result = test_item._get_test_parameter_key(mock_item)

        assert result == []

    def test_get_test_parameter_key_with_parametrize(self, mock_item):
        """Test _get_test_parameter_key with @pytest.mark.parametrize"""
        param_marker = Mock()
        param_marker.args = ["param1,param2"]

        mock_item.iter_markers.side_effect = lambda name: iter([param_marker]) if name == 'parametrize' else iter([])

        test_item = TestItem.__new__(TestItem)

        result = test_item._get_test_parameter_key(mock_item)

        assert set(result) == {"param1", "param2"}

    def test_get_test_parameter_key_with_callspec(self, mock_item):
        """Test _get_test_parameter_key with callspec"""
        mock_item.iter_markers.return_value = iter([])
        mock_item.callspec = Mock()
        mock_item.callspec.params = {"fixture1": "value1", "fixture2": "value2"}

        test_item = TestItem.__new__(TestItem)

        result = test_item._get_test_parameter_key(mock_item)

        assert set(result) == {"fixture1", "fixture2"}

    def test_resolve_parameter_key_in_test_name(self, mock_item):
        """Test _resolve_parameter_key_in_test_name"""
        test_item = TestItem.__new__(TestItem)

        with patch.object(test_item, '_get_test_parameter_key', return_value=["param1", "param2"]):
            result = test_item._resolve_parameter_key_in_test_name(mock_item, "Test name[value]")

            assert result == "Test name ${param1} ${param2}"

    def test_resolve_parameter_key_no_params(self, mock_item):
        """Test _resolve_parameter_key_in_test_name without params"""
        test_item = TestItem.__new__(TestItem)

        with patch.object(test_item, '_get_test_parameter_key', return_value=[]):
            result = test_item._resolve_parameter_key_in_test_name(mock_item, "Test name")

            assert result == "Test name"

    def test_to_string_value_various_types(self, mock_item):
        """Test _to_string_value with different types"""
        test_item = TestItem.__new__(TestItem)

        assert test_item._to_string_value("string") == "string"
        assert test_item._to_string_value(123) == "123"
        assert test_item._to_string_value(12.34) == "12.34"
        assert test_item._to_string_value(True) == "True"
        assert test_item._to_string_value(None) == "None"

        assert test_item._to_string_value(b"bytes") == "bytes"

        def test_func():
            pass

        assert test_item._to_string_value(test_func) == "test_func"

    def test_safe_params(self, mock_item):
        """Test safe_params"""
        test_item = TestItem.__new__(TestItem)

        params = {
            "str_param": "value",
            "int_param": 42,
            "bytes_param": b"bytes_value",
            "none_param": None
        }

        result = test_item.safe_params(params)

        expected = {
            "str_param": "value",
            "int_param": "42",
            "bytes_param": "bytes_value",
            "none_param": "None"
        }

        assert result == expected

    @patch('inspect.getsource')
    def test_to_dict(self, mock_getsource, mock_item):
        """Test to_dict method"""
        mock_getsource.return_value = "def test(): pass"
        mock_item.stash.get.return_value = ["artifact1.png"]

        test_item = TestItem(mock_item)
        result = test_item.to_dict()

        expected_keys = [
            'uid', 'id', 'title', 'fileName', 'absolutePath',
            'filePath', 'module', 'className', 'sourceCode', 'artifacts'
        ]

        for key in expected_keys:
            assert key in result

        assert result['title'] == "test_example"
        assert result['fileName'] == "test_file.py"
        assert result['module'] == "test_module"
        assert result['artifacts'] == ["artifact1.png"]

    @patch('inspect.getsource')
    def test_json_method(self, mock_getsource, mock_item):
        """Test json method"""
        mock_getsource.return_value = "def test(): pass"

        test_item = TestItem(mock_item)
        json_result = test_item.json()

        parsed = json.loads(json_result)
        assert isinstance(parsed, dict)
        assert 'title' in parsed

    @patch('inspect.getsource')
    def test_str_and_repr(self, mock_getsource, mock_item_with_marker):
        """Test __str__ and __repr__"""
        mock_getsource.return_value = "def test(): pass"

        test_item = TestItem(mock_item_with_marker)

        str_result = str(test_item)
        repr_result = repr(test_item)

        expected = "TestItem: @T12345678 - test_example - test_file.py"
        assert str_result == expected
        assert repr_result == expected

    def test_resolve_parameter_value_in_test_name(self, mock_item):
        """Test _resolve_parameter_value_in_test_name method"""
        test_item = TestItem.__new__(TestItem)

        mock_item.callspec = Mock()
        mock_item.callspec.params = {"param1": "value1", "param2": "value with spaces"}

        with patch.object(test_item, '_get_test_parameter_key', return_value=["param1", "param2"]):
            with patch.object(test_item, '_get_sync_test_title', return_value="Test ${param1} and ${param2}"):
                result = test_item._resolve_parameter_value_in_test_name(mock_item, "Test name")

                assert "value1" in result
                assert "value_with_spaces" in result

    @patch("inspect.getsource")
    def test_resolve_parameter_value_no_callspec(self, mock_source, mock_item):
        """Test _resolve_parameter_value_in_test_name without callspec"""
        test_item = TestItem(mock_item)
        mock_item.callspec = None

        with patch.object(test_item, '_get_test_parameter_key', return_value=["param1"]):
            result = test_item._resolve_parameter_value_in_test_name(mock_item, "Test name")

            assert result == "Test name"

    @patch('inspect.getsource')
    def test_get_regular_type(self, mock_getsource, mock_item):
        mock_getsource.return_value = "def test(): pass"
        test_item = TestItem(mock_item)
        assert test_item.type == 'regular'

    @patch('inspect.getsource')
    def test_get_bdd_type(self, mock_getsource, mock_item):
        mock_getsource.return_value = "def test(): pass"
        mock_item.function.__scenario__ = True
        test_item = TestItem(mock_item)
        assert test_item.type == 'bdd'

    @patch('inspect.getsource')
    def test_suite_title_for_regular_test(self, mock_getsource, mock_item):
        mock_getsource.return_value = "def test(): pass"
        test_item = TestItem(mock_item)
        assert test_item.suite_title == 'test_file.py'

    @patch('inspect.getsource')
    def test_suite_title_for_bdd_test(self, mock_getsource, mock_item):
        mock_getsource.return_value = "def test(): pass"
        scenario_mock = Mock()
        feature_mock = Mock()
        feature_mock.name = 'Test feature'
        scenario_mock.feature = feature_mock
        mock_item.function.__scenario__ = scenario_mock
        test_item = TestItem(mock_item)
        assert test_item.suite_title == 'Test feature'

    @patch('inspect.getsource')
    def test_suite_title_return_filename_for_bdd_test(self, mock_getsource, mock_item):
        """Test suite title returns filename for bdd test if feature unavailable"""
        mock_getsource.return_value = "def test(): pass"
        scenario_mock = Mock(spec=[])
        mock_item.function.__scenario__ = scenario_mock
        test_item = TestItem(mock_item)
        assert test_item.suite_title == 'test_file.py'
