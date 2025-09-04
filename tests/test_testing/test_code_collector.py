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

    def test_get_functions_source_no_matches(self, multiple_test_items):
        """Test functions not matches"""
        all_tests = ['nonexistent_function', 'another_missing_function']
        path = multiple_test_items[0].path

        results = list(get_functions_source_by_name(path, all_tests))

        assert len(results) == 0
