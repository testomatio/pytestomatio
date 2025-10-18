import pytest
import tempfile
import os
from pathlib import Path
import libcst as cst

from pytestomatio.decor.default import DecoratorUpdater, DecoratorRemover, update_tests


class TestDecoratorUpdater:
    """Tests for DecoratorUpdater"""

    def test_get_id_by_title_found(self):
        """Test get ID by title"""
        mapped_tests = [("test_one", "@T123", "file1"), ("test_two", "@T456", "file1")]
        updater = DecoratorUpdater(mapped_tests, [], "testomatio", "path/file1")

        result = updater._get_id_by_title("test_one")
        assert result == "@T123"

    def test_get_id_by_title_not_found(self):
        """Test title not found"""
        mapped_tests = [("test_one", "@T123", "file1")]
        updater = DecoratorUpdater(mapped_tests, [], "testomatio", "path/file1")

        result = updater._get_id_by_title("nonexistent")
        assert result is None

    def test_get_id_by_title_not_found_if_file_not_match(self):
        """Test title not found"""
        mapped_tests = [("test_one", "@T123", "file1")]
        updater = DecoratorUpdater(mapped_tests, [], "testomatio", "path/file2")

        result = updater._get_id_by_title("@T123")
        assert result is None

    def test_basic_decorator_addition(self):
        """Test add decorator to function"""
        source_code = '''
def test_example():
    assert True
'''

        tree = cst.parse_module(source_code)
        assert '@pytest.mark.testomatio("@T123")' not in tree.code


        updater = DecoratorUpdater([("test_example", "@T123", "file1")], ["test_example"], "testomatio", "path/file1")

        modified_tree = tree.visit(updater)
        result_code = modified_tree.code

        assert '@pytest.mark.testomatio("@T123")' in result_code
        assert 'def test_example():' in result_code

    def test_decorator_not_added_if_not_in_all_tests(self):
        """Test decorator not added if function not in all_tests"""
        source_code = '''
def test_example():
    assert True
'''

        tree = cst.parse_module(source_code)
        updater = DecoratorUpdater([("test_example", "@T123", "file1")], [], "testomatio", "path/file1")  # порожній all_tests

        modified_tree = tree.visit(updater)
        result_code = modified_tree.code

        assert '@pytest.mark.testomatio' not in result_code

    def test_decorator_not_duplicated(self):
        """Test decorator not duplicated if already exists"""
        source_code = '''
@pytest.mark.testomatio("@T123")
def test_example():
    assert True
'''

        tree = cst.parse_module(source_code)
        updater = DecoratorUpdater([("test_example", "@T456", "file1")], ["test_example"], "testomatio", 'path/file1')

        modified_tree = tree.visit(updater)
        result_code = modified_tree.code

        assert result_code.count('@pytest.mark.testomatio') == 1


class TestDecoratorRemover:
    """Tests for DecoratorRemover"""

    def test_removes_testomatio_decorator(self):
        """Test remove testomatio decorator"""
        source_code = '''
@pytest.mark.testomatio("@T123")
def test_example():
    assert True
'''

        tree = cst.parse_module(source_code)
        remover = DecoratorRemover("testomatio")

        modified_tree = tree.visit(remover)
        result_code = modified_tree.code

        assert '@pytest.mark.testomatio' not in result_code
        assert 'def test_example():' in result_code

    def test_preserves_other_decorators(self):
        """Test other decorators remain"""
        source_code = '''
@pytest.mark.skip
@pytest.mark.testomatio("@T123")
@pytest.mark.parametrize("param", [1, 2])
def test_example():
    assert True
'''

        tree = cst.parse_module(source_code)
        remover = DecoratorRemover("testomatio")

        modified_tree = tree.visit(remover)
        result_code = modified_tree.code

        assert '@pytest.mark.testomatio' not in result_code
        assert '@pytest.mark.skip' in result_code
        assert '@pytest.mark.parametrize' in result_code


class TestUpdateTestsIntegration:
    """Integration tests for update_tests function"""

    @pytest.fixture
    def temp_test_file(self):
        content = '''
def test_one():
    assert True

def test_two():
    assert False
'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            temp_path = f.name

        yield temp_path
        os.unlink(temp_path)

    def test_update_tests_adds_decorators(self, temp_test_file):
        """Test update_tests adds decorators"""
        filename = Path(temp_test_file).name
        mapped_tests = [("test_one", "@T123", filename), ("test_two", "@T456", filename)]
        all_tests = ["test_one", "test_two"]

        update_tests(temp_test_file, mapped_tests, all_tests, "testomatio", remove=False)

        with open(temp_test_file, 'r') as f:
            result = f.read()

        assert '@pytest.mark.testomatio("@T123")' in result
        assert '@pytest.mark.testomatio("@T456")' in result

    def test_update_tests_removes_decorators(self, temp_test_file):
        """Test update_tests removes decorators"""
        content_with_decorators = '''
@pytest.mark.testomatio("@T123")
def test_one():
    assert True

@pytest.mark.testomatio("@T456")
def test_two():
    assert False
'''

        with open(temp_test_file, 'w') as f:
            f.write(content_with_decorators)

        update_tests(temp_test_file, [], [], "testomatio", remove=True)

        with open(temp_test_file, 'r') as f:
            result = f.read()

        assert '@pytest.mark.testomatio' not in result
        assert 'def test_one():' in result
        assert 'def test_two():' in result
