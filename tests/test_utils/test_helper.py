import os
from unittest.mock import Mock, patch, call

from pytestomatio.utils.helper import collect_tests, get_test_mapping, parse_test_list, add_and_enrich_tests, \
    read_env_s3_keys
from pytestomatio.testing.testItem import TestItem
from pytestomatio.testomatio.testomat_item import TestomatItem


class TestCollectTests:
    """Tests for collect_tests function"""

    def test_collect_tests_empty_list(self):
        """Test empty items"""
        result_meta, result_files, result_names = collect_tests([])

        assert result_meta == []
        assert result_files == set()
        assert result_names == []

    def test_collect_tests_single_item(self, single_test_item):
        """Test processing single pytest item"""
        item = single_test_item[0]
        with patch('pytestomatio.utils.helper.get_functions_source_by_name') as mock_get_source:
            mock_get_source.return_value = [('addition', 'def test_addition():\n    assert 1 + 1 == 2')]

            meta, test_files, test_names = collect_tests([item])

            assert len(meta) == 1
            assert len(test_files) == 1
            assert len(test_names) == 1

            assert isinstance(meta[0], TestItem)
            assert 'addition' in test_names[0]

    def test_collect_tests_multiple_items_same_file(self, multiple_test_items):
        """Test processing multiple test from one file"""

        with patch('pytestomatio.utils.helper.get_functions_source_by_name') as mock_get_source:
            mock_get_source.return_value = [
                ('division', 'def test_division():\n    assert 2 / 2 == 1'),
                ('first', 'def test_first(): assert True')
            ]

            meta, test_files, test_names = collect_tests(multiple_test_items)

            assert len(meta) == 3
            assert len(test_files) == 1
            assert len(test_names) == 3

    def test_collect_tests_multiple_files(self, single_test_item, multiple_test_items):
        """Test processing test from different files"""

        all_items = single_test_item + multiple_test_items

        with patch('pytestomatio.utils.helper.get_functions_source_by_name') as mock_get_source:
            def side_effect(file_path, test_names):
                if 'test_single.py' in str(file_path):
                    return [('addition', 'def test_addition():\n    assert 1 + 1 == 2')]
                elif 'test_multiple.py' in str(file_path):
                    return [
                        ('division', 'def test_division():\n    assert 2 / 2 == 1'),
                        ('first', 'def test_first(): assert True')
                            ]
                return []

            mock_get_source.side_effect = side_effect
            meta, test_files, test_names = collect_tests(all_items)

            assert len(meta) == 4
            assert len(test_files) == 2
            assert len(test_names) == 4

    def test_collect_tests_parametrized_deduplication(self, multiple_test_items):
        """Test parametrized tests deduplication"""

        collected_test_number = len(multiple_test_items)
        with patch('pytestomatio.utils.helper.get_functions_source_by_name') as mock_get_source:
            mock_get_source.return_value = [
                ('division', 'def test_division():\n    assert 2 / 2 == 1'),
                ('first', 'def test_first(): assert True')
            ]
        meta, test_files, test_names = collect_tests(multiple_test_items)

        assert len(meta) == 3
        assert len(test_files) == 1
        assert len(test_names) == 3
        assert len(meta) != collected_test_number

    def test_collect_tests_source_code_assignment(self, single_test_item):
        """Test source code assignment to TestItem"""
        expected_source_code = '''    
                @pytest.mark.testomatio("@T12345678")
                def test_addition():
                    """Test basic addition"""
                    assert 1 + 1 == 2'''
        with patch('pytestomatio.utils.helper.get_functions_source_by_name') as mock_get_source:
            mock_get_source.return_value = [('addition', expected_source_code)]
        meta, test_files, test_names = collect_tests(single_test_item)

        assert len(meta) == 1
        test_item = meta[0]
        assert '@T12345678' in test_item.source_code
        assert '@T12345678' in expected_source_code

    def test_collect_tests_source_code_not_found(self, single_test_item):
        """Test source code not found in file"""
        different_code = 'some_code'
        with patch('pytestomatio.utils.helper.get_functions_source_by_name') as mock_get_source:
            mock_get_source.return_value = [('different_name', different_code)]
            meta, test_files, test_names = collect_tests(single_test_item)

        assert len(meta) == 1
        test_item = meta[0]
        assert test_item.source_code is not None
        assert different_code not in test_item.source_code

    def test_collect_tests_preserves_test_item_attributes(self, single_test_item):
        """Test attributes collected correctly in TestItem"""
        with patch('pytestomatio.utils.helper.get_functions_source_by_name') as mock_get_source:

            mock_get_source.return_value = [('addition', 'def test_addition():\n    assert 1 + 1 == 2')]
            meta, test_files, test_names = collect_tests(single_test_item)

            assert len(meta) == 1
            test_item = meta[0]

            assert test_item.id == '@T12345678'
            assert 'addition' in test_item.title
            assert test_item.file_name.endswith('.py')
            assert isinstance(test_files, set)
            assert test_item.abs_path is not None
            assert test_item.abs_path in test_files

    def test_collect_tests_return_types(self, single_test_item):
        """Test collected types"""

        with patch('pytestomatio.utils.helper.get_functions_source_by_name') as mock_get_source:
            mock_get_source.return_value = [('addition', 'def test_addition():\n    assert 1 + 1 == 2')]
            meta, test_files, test_names = collect_tests(single_test_item)

            assert isinstance(meta, list)
            assert isinstance(test_files, set)
            assert isinstance(test_names, list)
            assert all(isinstance(item, TestItem) for item in meta)
            assert all(isinstance(path, str) for path in test_files)
            assert all(isinstance(name, str) for name in test_names)


class TestCollectTestsEdgeCases:
    """Edge cases for collect_tests function"""

    @patch('pytestomatio.utils.helper.get_functions_source_by_name')
    def test_collect_tests_empty_source_pairs(self, mock_get_source, single_test_item):
        """Test get_functions_source_by_name returns empty list"""

        mock_get_source.return_value = []

        meta, test_files, test_names = collect_tests(single_test_item)

        assert len(meta) == 1
        assert len(test_files) == 1
        assert len(test_names) == 1


class TestGetTestMapping:
    """Test for get_test_mapping function"""

    def test_get_test_mapping_empty_list(self):
        result = get_test_mapping([])

        assert result == []
        assert isinstance(result, list)

    def test_get_test_mapping_single_test_item(self):
        """Test with one TestItem"""
        mock_test_item = Mock(spec=TestItem)
        mock_test_item.title = "Test Addition"
        mock_test_item.id = "@T12345678"

        result = get_test_mapping([mock_test_item])

        assert result == [("Test Addition", "@T12345678")]
        assert len(result) == 1
        assert isinstance(result[0], tuple)

    def test_get_test_mapping_multiple_test_items(self):
        """Test with multiple TestItem"""
        mock_items = []

        test_data = [
            ("Test Login", "@T11111111"),
            ("Test Logout", "@T22222222"),
            ("Test Registration", "@T33333333")
        ]

        for title, test_id in test_data:
            mock_item = Mock(spec=TestItem)
            mock_item.title = title
            mock_item.id = test_id
            mock_items.append(mock_item)

        result = get_test_mapping(mock_items)

        expected = [
            ("Test Login", "@T11111111"),
            ("Test Logout", "@T22222222"),
            ("Test Registration", "@T33333333")
        ]

        assert result == expected
        assert len(result) == 3
        assert all(isinstance(item, tuple) for item in result)

    def test_get_test_mapping_test_items_without_id(self):
        """Test TestItem without ID (None)"""
        mock_test_item = Mock(spec=TestItem)
        mock_test_item.title = "Test Without ID"
        mock_test_item.id = None

        result = get_test_mapping([mock_test_item])

        assert result == [("Test Without ID", None)]


class TestParseTestList:
    """Tests for parse_test_list function"""

    def test_parse_test_list_empty_response(self):
        """Test with empty response"""
        raw_response = {
            "tests": {},
            "suites": {},
            "files": {}
        }

        result = parse_test_list(raw_response)

        assert result == []
        assert isinstance(result, list)

    def test_parse_test_list_test_with_suite(self):
        """Test parse test with suite"""
        raw_response = {
            "tests": {
                "Test Suite#Test Name": "@T12345678"
            },
            "suites": {
                "Test Suite": "@S11111111"
            },
            "files": {}
        }

        with patch('pytestomatio.utils.helper.TestomatItem') as MockTestomatItem:
            parse_test_list(raw_response)

            MockTestomatItem.assert_called_once_with("@T12345678", "Test Name", None)

    def test_parse_test_list_test_with_file_suite_name(self):
        """Тest with full structure"""
        raw_response = {
            "tests": {
                "test_file.py#Test Suite#Test Name": "@T12345678"
            },
            "suites": {
                "Test Suite": "@S11111111"
            },
            "files": {}
        }

        with patch('pytestomatio.utils.helper.TestomatItem') as MockTestomatItem:
            parse_test_list(raw_response)

            MockTestomatItem.assert_called_once_with("@T12345678", "Test Name", "test_file.py")

    def test_parse_test_list_real_json_example(self):
        """Test real JSON"""
        raw_response = {
            "tests": {
                "test_cli_params.py#Test cli params.py#Smoke": "@T55ecbca9",
                "Test cli params.py#Smoke": "@T55ecbca9",
                "Smoke": "@T55ecbca9",
                "test_cli_params.py#Test cli params.py#Testomatio only": "@Ta8639cd0",
                "Test cli params.py#Testomatio only": "@Ta8639cd0",
                "Testomatio only": "@Ta8639cd0"
            },
            "suites": {
                "test_cli_params.py#Test cli params.py": "@S2c57ff3d",
                "Test cli params.py": "@S2c57ff3d"
            },
            "files": {}
        }

        with patch('pytestomatio.utils.helper.TestomatItem') as MockTestomatItem:
            result = parse_test_list(raw_response)

            assert MockTestomatItem.call_count == 2
            calls = MockTestomatItem.call_args_list
            call_args = [call[0] for call in calls]

            assert ("@T55ecbca9", "Smoke", "test_cli_params.py") in call_args
            assert ("@Ta8639cd0", "Testomatio only", "test_cli_params.py") in call_args


class TestAddAndEnrichTests:
    """Test for add_and_enrich_tests function"""

    @patch('pytestomatio.utils.helper.update_tests')
    @patch('pytestomatio.utils.helper.get_test_mapping')
    @patch('pytestomatio.utils.helper.parse_test_list')
    def test_add_and_enrich_tests_no_matches(self, mock_parse, mock_mapping, mock_update):
        """Test no matches betweeb collected test metadata and testomatio_tests"""
        mock_meta_item = Mock(spec=TestItem)
        mock_meta_item.resync_title = "Test One"
        mock_meta_item.file_name = "test_file1.py"
        mock_meta_item.id = None

        mock_tcm_item = Mock(spec=TestomatItem)
        mock_tcm_item.title = "Different Test"
        mock_tcm_item.file_name = "test_file2.py"
        mock_tcm_item.id = "@T12345678"

        mock_parse.return_value = [mock_tcm_item]
        mock_mapping.return_value = [("Test One", None)]

        add_and_enrich_tests(
            meta=[mock_meta_item],
            test_files={"/path/to/test_file1.py"},
            test_names=["Test One"],
            testomatio_tests={"tests": {}},
            decorator_name="testomatio"
        )

        assert mock_meta_item.id is None

        mock_parse.assert_called_once_with({"tests": {}})
        mock_mapping.assert_called_once_with([mock_meta_item])
        mock_update.assert_called_once_with(
            "/path/to/test_file1.py",
            [("Test One", None)],
            ["Test One"],
            "testomatio"
        )

    @patch('pytestomatio.utils.helper.update_tests')
    @patch('pytestomatio.utils.helper.get_test_mapping')
    @patch('pytestomatio.utils.helper.parse_test_list')
    def test_add_and_enrich_tests_exact_match(self, mock_parse, mock_mapping, mock_update):
        """Test match between meta and testomatio test"""
        # Meta test
        mock_meta_item = Mock(spec=TestItem)
        mock_meta_item.resync_title = "Login Test"
        mock_meta_item.file_name = "test_auth.py"
        mock_meta_item.id = None

        # Testomatio test
        mock_tcm_item = Mock(spec=TestomatItem)
        mock_tcm_item.title = "Login Test"
        mock_tcm_item.file_name = "test_auth.py"
        mock_tcm_item.id = "@T12345678"

        mock_parse.return_value = [mock_tcm_item]
        mock_mapping.return_value = [("Login Test", "@T12345678")]

        add_and_enrich_tests(
            meta=[mock_meta_item],
            test_files={"/path/to/test_auth.py"},
            test_names=["Login Test"],
            testomatio_tests={"tests": {}},
            decorator_name="testomatio"
        )

        assert mock_meta_item.id == "@T12345678"
        assert not mock_parse.return_value

    @patch('pytestomatio.utils.helper.update_tests')
    @patch('pytestomatio.utils.helper.get_test_mapping')
    @patch('pytestomatio.utils.helper.parse_test_list')
    @patch('pytestomatio.utils.helper.basename')
    def test_add_and_enrich_tests_basename_match(self, mock_basename, mock_parse, mock_mapping, mock_update):
        """Test id updated if basename match(same filenames, different paths)"""
        # Meta test
        mock_meta_item = Mock(spec=TestItem)
        mock_meta_item.resync_title = "Api Test"
        mock_meta_item.file_name = "/src/tests/test_api.py"
        mock_meta_item.id = None

        # Testomatio
        mock_tcm_item = Mock(spec=TestomatItem)
        mock_tcm_item.title = "Api Test"
        mock_tcm_item.file_name = "/different/path/test_api.py"
        mock_tcm_item.id = "@T87654321"

        mock_basename.side_effect = lambda x: "test_api.py"

        mock_parse.return_value = [mock_tcm_item]
        mock_mapping.return_value = [("Api Test", "@T87654321")]

        add_and_enrich_tests(
            meta=[mock_meta_item],
            test_files={"/src/tests/test_api.py"},
            test_names=["Api Test"],
            testomatio_tests={"tests": {}},
            decorator_name="testomatio"
        )

        assert mock_basename.call_count == 2
        mock_basename.assert_any_call("/src/tests/test_api.py")
        mock_basename.assert_any_call("/different/path/test_api.py")

        assert mock_meta_item.id == "@T87654321"

    @patch('pytestomatio.utils.helper.update_tests')
    @patch('pytestomatio.utils.helper.get_test_mapping')
    @patch('pytestomatio.utils.helper.parse_test_list')
    def test_add_and_enrich_tests_skip_no_file_name(self, mock_parse, mock_mapping, mock_update):
        """Test skip if testomatio tests without filenames"""
        mock_meta_item = Mock(spec=TestItem)
        mock_meta_item.resync_title = "Some Test"
        mock_meta_item.file_name = "test.py"
        mock_meta_item.id = None

        mock_tcm_item = Mock(spec=TestomatItem)
        mock_tcm_item.title = "Some Test"
        mock_tcm_item.file_name = None
        mock_tcm_item.id = "@T99999999"

        mock_parse.return_value = [mock_tcm_item]
        mock_mapping.return_value = [("Some Test", None)]

        add_and_enrich_tests(
            meta=[mock_meta_item],
            test_files={"test.py"},
            test_names=["Some Test"],
            testomatio_tests={"tests": {}},
            decorator_name="testomatio"
        )

        assert mock_meta_item.id is None

    @patch('pytestomatio.utils.helper.update_tests')
    @patch('pytestomatio.utils.helper.get_test_mapping')
    @patch('pytestomatio.utils.helper.parse_test_list')
    def test_add_and_enrich_tests_multiple_files_and_tests(self, mock_parse, mock_mapping, mock_update):
        """Test with multiple files and tests"""
        meta_items = []
        for title, file_name in [("Test A", "file1.py"), ("Test B", "file2.py")]:
            item = Mock(spec=TestItem)
            item.resync_title = title
            item.file_name = file_name
            item.id = None
            meta_items.append(item)

        tcm_items = []
        for title, file_name, test_id in [("Test A", "file1.py", "@T111"), ("Test B", "file2.py", "@T222")]:
            item = Mock(spec=TestomatItem)
            item.title = title
            item.file_name = file_name
            item.id = test_id
            tcm_items.append(item)

        mock_parse.return_value = tcm_items
        mock_mapping.return_value = [("Test A", "@T111"), ("Test B", "@T222")]

        test_files = {"file1.py", "file2.py"}

        add_and_enrich_tests(
            meta=meta_items,
            test_files=test_files,
            test_names=["Test A", "Test B"],
            testomatio_tests={"tests": {}},
            decorator_name="testomatio"
        )

        assert meta_items[0].id == "@T111"
        assert meta_items[1].id == "@T222"

        assert mock_update.call_count == 2

        expected_calls = [
            call("file1.py", [("Test A", "@T111"), ("Test B", "@T222")], ["Test A", "Test B"], "testomatio"),
            call("file2.py", [("Test A", "@T111"), ("Test B", "@T222")], ["Test A", "Test B"], "testomatio")
        ]
        mock_update.assert_has_calls(expected_calls, any_order=True)

    @patch('pytestomatio.utils.helper.update_tests')
    @patch('pytestomatio.utils.helper.get_test_mapping')
    @patch('pytestomatio.utils.helper.parse_test_list')
    def test_add_and_enrich_tests_partial_matches(self, mock_parse, mock_mapping, mock_update):
        """Test partial test matches"""
        meta1 = Mock(spec=TestItem)
        meta1.resync_title = "Found Test"
        meta1.file_name = "test.py"
        meta1.id = None

        meta2 = Mock(spec=TestItem)
        meta2.resync_title = "Not Found Test"
        meta2.file_name = "test.py"
        meta2.id = None

        # Only one testomatio test
        tcm_item = Mock(spec=TestomatItem)
        tcm_item.title = "Found Test"
        tcm_item.file_name = "test.py"
        tcm_item.id = "@T12345678"

        mock_parse.return_value = [tcm_item]
        mock_mapping.return_value = [("Found Test", "@T12345678"), ("Not Found Test", None)]

        add_and_enrich_tests(
            meta=[meta1, meta2],
            test_files={"test.py"},
            test_names=["Found Test", "Not Found Test"],
            testomatio_tests={"tests": {}},
            decorator_name="testomatio"
        )

        assert meta1.id == "@T12345678"
        assert meta2.id is None


class TestReadEnvS3Keys:
    """Test for read_env_s3_keys function"""

    def test_read_env_s3_keys_empty_config_and_env(self):
        """Test with empty config and env"""
        with patch.dict(os.environ, {}, clear=True):
            result = read_env_s3_keys({})

            expected = (None, None, None, None, None, None, "public-read")
            assert result == expected
