import pytest
import tempfile
import os
import ast

from pytestomatio.decor.pep8 import DecoratorUpdater, update_tests


class TestDecoratorUpdaterPep8:
    """Test for PEP8 DecoratorUpdater"""

    def test_get_id_by_title_found(self):
        """Test found ID by title"""
        mapped_tests = [("test_login", "@T123", "file1"), ("test_logout", "@T456", "file1")]
        updater = DecoratorUpdater(mapped_tests, [], "testomatio", "path/file1")

        result = updater._get_id_by_title("test_login")
        assert result == "@T123"

    def test_get_id_by_title_not_found(self):
        """Test title not found"""
        mapped_tests = [("test_login", "@T123", "file1")]
        updater = DecoratorUpdater(mapped_tests, [], "testomatio", "path/file1")

        result = updater._get_id_by_title("missing_test")
        assert result is None

    def test_get_id_by_title_not_found_if_filename_not_match(self):
        """Test title not found"""
        mapped_tests = [("test_login", "@T123", "file2")]
        updater = DecoratorUpdater(mapped_tests, [], "testomatio", "path/file1")

        result = updater._get_id_by_title("@T123")
        assert result is None

    def test_visit_function_def_adds_decorator(self):
        """Test add decorator to function"""
        source_code = '''
def test_example():
   assert True
'''

        tree = ast.parse(source_code)
        assert "mark.testomatio('@T123')" not in tree.body

        updater = DecoratorUpdater([("test_example", "@T123", "file1")], ["test_example"], "testomatio", "path/file1")

        func_node = tree.body[0]
        assert isinstance(func_node, ast.FunctionDef)

        updated_node = updater.visit_FunctionDef(func_node)

        assert len(updated_node.decorator_list) == 1
        decorator = updated_node.decorator_list[0]
        assert isinstance(decorator, ast.Name)
        assert "mark.testomatio('@T123')" in decorator.id

    def test_visit_function_def_skips_if_not_in_all_tests(self):
        """Test decorator not added if function not in all_tests"""
        source_code = '''
def test_example():
   assert True
'''

        tree = ast.parse(source_code)
        updater = DecoratorUpdater([("test_example", "@T123", "file1")], [], "testomatio", "path/file1")  # порожній all_tests

        func_node = tree.body[0]
        updated_node = updater.visit_FunctionDef(func_node)

        assert len(updated_node.decorator_list) == 0

    def test_visit_function_def_skips_if_decorator_exists(self):
        """Test decorator not added if already exists"""
        tree = ast.parse('''
@pytest.mark.testomatio("@T456")
def test_example():
   assert True
''')

        updater = DecoratorUpdater([("test_example", "@T123", "file1")], ["test_example"], "testomatio", "path/file1")

        func_node = tree.body[0]
        original_decorators_count = len(func_node.decorator_list)

        updated_node = updater.visit_FunctionDef(func_node)

        assert len(updated_node.decorator_list) == original_decorators_count

    def test_remove_decorator(self):
        """Test decorator remove"""
        tree = ast.parse('''
@pytest.mark.testomatio("@T123")
def test_example():
   assert True
''')

        updater = DecoratorUpdater([], [], "testomatio", "path/file1")
        func_node = tree.body[0]

        updated_node = updater._remove_decorator(func_node)

        assert len(updated_node.decorator_list) == 0

    def test_remove__other_decorators_reamin_method(self):
        """Test other decorator remains"""
        tree = ast.parse('''
@pytest.mark.testomatio("@T123")
def test_one():
   assert True

@pytest.mark.skip
@pytest.mark.testomatio("@T456")
def test_two():
   assert False
''')

        updater = DecoratorUpdater([], [], "testomatio", "path/file1")

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                updater.visit_FunctionDef(node, remove=True)

        func_one = tree.body[0]
        func_two = tree.body[1]

        assert len(func_one.decorator_list) == 0
        assert len(func_two.decorator_list) == 1


class TestUpdateTestsPep8Integration:
    """Integration test for PEP8 update_tests function"""

    @pytest.fixture
    def temp_test_file(self):
        content = '''
def test_addition():
   result = 1 + 1
   assert result == 2

def test_subtraction():
   result = 5 - 3
   assert result == 2
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_path = f.name

        yield temp_path
        os.unlink(temp_path)

    def test_update_tests_adds_decorators_and_import(self, temp_test_file):
        """Test update_tests add decorators and import"""
        filename = temp_test_file.split('/')[-1]
        mapped_tests = [("test_addition", "@T123", filename), ("test_subtraction", "@T456", filename)]
        all_tests = ["test_addition", "test_subtraction"]

        update_tests(temp_test_file, mapped_tests, all_tests, "testomatio", remove=False)

        with open(temp_test_file, 'r') as f:
            result = f.read()

        assert "from pytest import mark" in result

        assert "mark.testomatio('@T123')" in result
        assert "mark.testomatio('@T456')" in result

        assert "def test_addition():" in result
        assert "def test_subtraction():" in result

    def test_update_tests_removes_decorators(self, temp_test_file):
        """Test update tests removes decorators"""
        content_with_decorators = '''
from pytest import mark

@mark.testomatio('@T123')
def test_addition():
   assert True

@mark.testomatio('@T456') 
def test_subtraction():
   assert False
'''

        with open(temp_test_file, 'w') as f:
            f.write(content_with_decorators)

        update_tests(temp_test_file, [], [], "testomatio", remove=True)

        with open(temp_test_file, 'r') as f:
            result = f.read()

        assert "mark.testomatio" not in result
        assert "def test_addition():" in result
        assert "def test_subtraction():" in result

    def test_update_tests_applies_pep8_formatting(self, temp_test_file):
        """Test PEP8 formatting applied"""
        badly_formatted = '''
def test_bad_formatting( ):
   x=1+2
   y   =   3*4
   assert x+y==15
'''

        with open(temp_test_file, 'w') as f:
            f.write(badly_formatted)

        filename = temp_test_file.split('/')[-1]
        mapped_tests = [("test_bad_formatting", "@T123", filename)]
        all_tests = ["test_bad_formatting"]

        update_tests(temp_test_file, mapped_tests, all_tests, "testomatio", remove=False)

        with open(temp_test_file, 'r') as f:
            result = f.read()

        assert "def test_bad_formatting():" in result
        assert "x = 1 + 2" in result
        assert "y = 3 * 4" in result
        assert "x + y == 15" in result

    def test_update_tests_preserves_existing_decorators(self, temp_test_file):
        """Test update tests preserver existing decorators"""
        content_with_other_decorators = '''
import pytest

@pytest.mark.skip(reason="Not implemented")
@pytest.mark.parametrize("param", [1, 2, 3])
def test_with_decorators():
   assert True
'''

        with open(temp_test_file, 'w') as f:
            f.write(content_with_other_decorators)

        filename = temp_test_file.split('/')[-1]
        mapped_tests = [("test_with_decorators", "@T789", filename)]
        all_tests = ["test_with_decorators"]

        update_tests(temp_test_file, mapped_tests, all_tests, "testomatio", remove=False)

        with open(temp_test_file, 'r') as f:
            result = f.read()

        assert "@pytest.mark.skip" in result or "mark.skip" in result
        assert "@pytest.mark.parametrize" in result or "mark.parametrize" in result
        assert "mark.testomatio('@T789')" in result
