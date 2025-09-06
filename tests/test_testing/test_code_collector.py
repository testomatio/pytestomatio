from unittest.mock import patch, Mock

from pytestomatio.testing.code_collector import get_bdd_function_source
from pytestomatio.utils.helper import get_functions_source_by_name


class TestGetFunctionsSourceByName:
    """Tests for get_functions_source_by_name"""

    def test_get_functions_source_single_function(self, single_test_item):
        """Test get source code for single function"""
        function_name, path = single_test_item[0].name, single_test_item[0].path
        all_tests = [function_name]

        results = list(get_functions_source_by_name(path, all_tests))

        assert len(results) == 1
        function_name, source_code = results[0]

        assert function_name == function_name
        assert 'def test_addition():' in source_code

    def test_get_functions_source_multiple_functions(self, multiple_test_items):
        """Test get source code for multiple functions"""
        all_tests = [item.name for item in multiple_test_items]
        path = multiple_test_items[0].path

        results = list(get_functions_source_by_name(path, all_tests))

        assert len(results) == 2

        function_names = [result[0] for result in results]
        assert 'test_division' in function_names
        assert 'test_first' in function_names

    def test_get_functions_source_with_pytest_bdd_functions(self, bdd_functions):
        """Test get source code for pytest bdd function"""
        all_tests = [item.name for item in bdd_functions]
        path = bdd_functions[0].path

        results = list(get_functions_source_by_name(path, all_tests))

        assert len(results) == 3

        function_names = [result[0] for result in results]
        assert 'test_bdd_generated' in function_names
        _, test_bdd_generated = results[0]
        assert 'def scenario_wrapper_generated():' in test_bdd_generated

        assert 'test_bdd_scenario' in function_names
        _, test_bdd_scenario = results[1]
        assert "def test_bdd_with_original():" in test_bdd_scenario

        assert 'test_first' in function_names
        _, test_first_source_code = results[-1]
        assert "def test_first()" in test_first_source_code

    def test_get_functions_source_no_matches(self, multiple_test_items):
        """Test functions not matches"""
        all_tests = ['nonexistent_function', 'another_missing_function']
        path = multiple_test_items[0].path

        results = list(get_functions_source_by_name(path, all_tests))

        assert len(results) == 0


class TestGetBddFunctionSource:

    def test_function_without_closure(self):
        """Test function without __closure__ attribute"""

        def test_regular_function():
            pass

        assert test_regular_function.__closure__ is None

        with patch('inspect.getsource', return_value='def test_regular_function(): pass'):
            result = get_bdd_function_source(test_regular_function)
            assert result == 'def test_regular_function(): pass'

    def test_function_with_empty_closure(self):
        """Test function with empty closure"""
        mock_func = Mock()
        mock_func.__closure__ = []

        with patch('inspect.getsource', return_value='wrapper code'):
            result = get_bdd_function_source(mock_func)
            assert result == 'wrapper code'

    def test_function_with_closure_containing_test_function(self):
        """Test function with closure containing a test function"""

        def test_original():
            pass

        mock_cell = Mock()
        mock_cell.cell_contents = test_original

        mock_func = Mock()
        mock_func.__closure__ = [mock_cell]

        result = get_bdd_function_source(mock_func)
        assert 'def test_original()' in result
        assert 'pass' in result

    def test_function_with_closure_no_test_functions(self):
        """Test function with closure but no test functions inside"""

        def helper_function():
            pass

        mock_cell = Mock()
        mock_cell.cell_contents = helper_function

        mock_func = Mock()
        mock_func.__closure__ = [mock_cell]

        with patch('inspect.getsource', return_value='wrapper code'):
            result = get_bdd_function_source(mock_func)
            assert result == 'wrapper code'

    def test_function_with_closure_non_callable_content(self):
        """Test function with closure containing non-callable objects"""
        mock_cell = Mock()
        mock_cell.cell_contents = "not a function"

        mock_func = Mock()
        mock_func.__closure__ = [mock_cell]

        with patch('inspect.getsource', return_value='wrapper code'):
            result = get_bdd_function_source(mock_func)
            assert result == 'wrapper code'

    def test_function_with_closure_callable_without_name(self):
        """Test function with closure containing callable without __name__"""
        mock_callable = Mock()
        del mock_callable.__name__

        mock_cell = Mock()
        mock_cell.cell_contents = mock_callable

        mock_func = Mock()
        mock_func.__closure__ = [mock_cell]

        with patch('inspect.getsource', return_value='wrapper code'):
            result = get_bdd_function_source(mock_func)
            assert result == 'wrapper code'

    def test_function_with_multiple_cells_first_is_test(self):
        """Test function with multiple closure cells, first one is test function"""

        def test_first():
            pass

        def test_second():
            pass

        mock_cell1 = Mock()
        mock_cell1.cell_contents = test_first

        mock_cell2 = Mock()
        mock_cell2.cell_contents = test_second

        mock_func = Mock()
        mock_func.__closure__ = [mock_cell1, mock_cell2]

        result = get_bdd_function_source(mock_func)
        assert 'test_first()' in result

    def test_function_with_multiple_cells_second_is_test(self):
        """Test function with multiple closure cells, second one is test function"""

        def helper():
            pass

        def test_second():
            pass

        mock_cell1 = Mock()
        mock_cell1.cell_contents = helper

        mock_cell2 = Mock()
        mock_cell2.cell_contents = test_second

        mock_func = Mock()
        mock_func.__closure__ = [mock_cell1, mock_cell2]

        result = get_bdd_function_source(mock_func)
        assert 'def test_second()' in result
