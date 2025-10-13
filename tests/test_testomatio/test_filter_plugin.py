import pytest
from unittest.mock import Mock, patch

from pytestomatio.testomatio.filter_plugin import TestomatioFilterPlugin


class TestTestomatioFilterPlugin:
    """Tests for TestomatioFilterPlugin"""

    @pytest.fixture
    def plugin(self):
        return TestomatioFilterPlugin()

    @pytest.fixture
    def mock_session(self):
        session = Mock()
        session._pytestomatio_original_collected_items = []
        return session

    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.getoption.return_value = None
        config.option = Mock()
        config.option.keyword = None
        config.option.markexpr = None
        config.option.last_failed = False
        config.option.ff = False
        config.option.lf = False
        return config

    def create_mock_item_with_marker(self, nodeid, marker_id):
        """Creates mock item with testomatio marker"""
        item = Mock()
        item.nodeid = nodeid

        marker = Mock()
        marker.args = [marker_id]
        item.iter_markers.return_value = iter([marker])
        return item

    def create_mock_item_without_marker(self, nodeid):
        """Creates mock item without testomatio marker"""
        item = Mock()
        item.nodeid = nodeid
        item.iter_markers.return_value = iter([])
        return item

    def test_no_testomatio_filter_option(self, plugin, mock_session, mock_config):
        """Test when no testomatio-filter option"""
        mock_config.getoption = Mock(return_value='report')
        items = [Mock(), Mock()]
        original_items = items.copy()

        plugin.pytest_collection_modifyitems(mock_session, mock_config, items)

        assert items == original_items
        mock_config.getoption.assert_called_with("testomatio_filter")

    @patch('pytestomatio.testomatio.filter_plugin.TestomatioFilterPlugin.get_matched_test_ids')
    def test_filter_incorrect_format(self, get_ids_mock, plugin, mock_session, mock_config, caplog):
        option_values = {
            'testomatio': 'report',
            'testomatio_filter': 'test_id'
        }
        mock_config.getoption.side_effect = lambda x: option_values.get(x)
        matched_item = self.create_mock_item_with_marker("test1", "@T12345678")
        unmatched_item = self.create_mock_item_with_marker("test2", "@T87654321")

        mock_session._pytestomatio_original_collected_items = [matched_item, unmatched_item]

        items = []
        plugin.pytest_collection_modifyitems(mock_session, mock_config, items)
        assert 'Incorrect filter format. Filter must be in type=value format.' in caplog.text
        assert get_ids_mock.call_count == 0

    @patch('pytestomatio.testomatio.filter_plugin.TestomatioFilterPlugin.get_matched_test_ids')
    def test_filter_one_of_values_empty(self, get_ids_mock, plugin, mock_session, mock_config, caplog):
        option_values = {
            'testomatio': 'report',
            'testomatio_filter': 'test_id='
        }
        mock_config.getoption.side_effect = lambda x: option_values.get(x)
        matched_item = self.create_mock_item_with_marker("test1", "@T12345678")
        unmatched_item = self.create_mock_item_with_marker("test2", "@T87654321")

        mock_session._pytestomatio_original_collected_items = [matched_item, unmatched_item]

        items = []
        plugin.pytest_collection_modifyitems(mock_session, mock_config, items)
        assert 'Failed to retrieve filter data.' in caplog.text
        assert get_ids_mock.call_count == 0

    @patch('pytestomatio.testomatio.filter_plugin.TestomatioFilterPlugin.get_matched_test_ids')
    def test_filter_not_allowed(self, get_ids_mock, plugin, mock_session, mock_config, caplog):
        f_type = 'random'
        option_values = {
            'testomatio': 'report',
            'testomatio_filter': f'{f_type}=T12345678'
        }
        mock_config.getoption.side_effect = lambda x: option_values.get(x)
        matched_item = self.create_mock_item_with_marker("test1", "@T12345678")
        unmatched_item = self.create_mock_item_with_marker("test2", "@T87654321")

        mock_session._pytestomatio_original_collected_items = [matched_item, unmatched_item]

        items = []
        plugin.pytest_collection_modifyitems(mock_session, mock_config, items)
        assert f"Filter '{f_type}' not allowed." in caplog.text
        assert get_ids_mock.call_count == 0

    def test_single_test_id_match(self, plugin, mock_session, mock_config):
        """Test with one matched test_id"""
        option_values = {
            'testomatio': 'report',
            'testomatio_filter': 'test_id=@T12345678'
        }
        mock_config.getoption.side_effect = lambda x: option_values.get(x)

        matched_item = self.create_mock_item_with_marker("test1", "@T12345678")
        unmatched_item = self.create_mock_item_with_marker("test2", "@T87654321")

        mock_session._pytestomatio_original_collected_items = [matched_item, unmatched_item]

        items = []
        plugin.pytest_collection_modifyitems(mock_session, mock_config, items)

        assert items == [matched_item]

    def test_multiple_test_ids_with_pipe_separator(self, plugin, mock_session, mock_config):
        """Test with multiple test_id"""
        option_values = {
            'testomatio': 'report',
            'testomatio_filter': 'test_id=@T12345678|@T87654321'
        }
        mock_config.getoption.side_effect = lambda x: option_values.get(x)

        item1 = self.create_mock_item_with_marker("test1", "@T12345678")
        item2 = self.create_mock_item_with_marker("test2", "@T87654321")
        item3 = self.create_mock_item_with_marker("test3", "@T99999999")

        mock_session._pytestomatio_original_collected_items = [item1, item2, item3]

        items = []

        plugin.pytest_collection_modifyitems(mock_session, mock_config, items)

        assert len(items) == 2
        assert item1 in items
        assert item2 in items
        assert item3 not in items

    def test_test_id_without_at_t_prefix(self, plugin, mock_session, mock_config):
        """Test test_id without @T prefix"""
        option_values = {
            'testomatio': 'report',
            'testomatio_filter': 'test_id=12345678'
        }
        mock_config.getoption.side_effect = lambda x: option_values.get(x)

        item = self.create_mock_item_with_marker("test1", "@T12345678")
        mock_session._pytestomatio_original_collected_items = [item]

        items = []

        plugin.pytest_collection_modifyitems(mock_session, mock_config, items)

        assert items == [item]

    def test_no_matching_items(self, plugin, mock_session, mock_config):
        """Test when no matching items"""
        option_values = {
            'testomatio': 'report',
            'testomatio_filter': 'test_id=@T12345678'
        }
        mock_config.getoption.side_effect = lambda x: option_values.get(x)

        item1 = self.create_mock_item_with_marker("test1", "@T99999999")
        item2 = self.create_mock_item_without_marker("test2")

        mock_session._pytestomatio_original_collected_items = [item1, item2]

        items = []

        plugin.pytest_collection_modifyitems(mock_session, mock_config, items)

        assert items == []

    def test_with_keyword_filter_active(self, plugin, mock_session, mock_config):
        """Test with active -k filter"""
        option_values = {
            'testomatio': 'report',
            'testomatio_filter': 'test_id=@T12345678'
        }
        mock_config.getoption.side_effect = lambda x: option_values.get(x)
        mock_config.option.keyword = "test_login"  # -k filter is active

        keyword_item = Mock()
        keyword_item.nodeid = "test_login"
        keyword_item.iter_markers.return_value = iter([])

        testomatio_item = self.create_mock_item_with_marker("test_auth", "@T12345678")

        mock_session._pytestomatio_original_collected_items = [keyword_item, testomatio_item]
        items = [keyword_item]

        plugin.pytest_collection_modifyitems(mock_session, mock_config, items)

        assert len(items) == 2
        assert keyword_item in items
        assert testomatio_item in items

    def test_with_markexpr_filter_active(self, plugin, mock_session, mock_config):
        """Test with -m filter"""
        option_values = {
            'testomatio': 'report',
            'testomatio_filter': 'test_id=@T12345678'
        }
        mock_config.getoption.side_effect = lambda x: option_values.get(x)
        mock_config.option.markexpr = "smoke"
        mock_config.option.keyword = ""

        mark_item = Mock()
        mark_item.iter_markers.return_value = iter([])
        testomatio_item = self.create_mock_item_with_marker("test", "@T12345678")

        mock_session._pytestomatio_original_collected_items = [mark_item, testomatio_item]

        items = [mark_item]

        plugin.pytest_collection_modifyitems(mock_session, mock_config, items)

        assert len(items) == 2
        assert mark_item in items
        assert testomatio_item in items

    def test_with_not_keyword_filter(self, plugin, mock_session, mock_config):
        """Test with "not" in keyword filter (exclusion logic)"""
        option_values = {
            'testomatio': 'report',
            'testomatio_filter': 'test_id=@T12345678'
        }
        mock_config.getoption.side_effect = lambda x: option_values.get(x)
        mock_config.option.keyword = "not slow"

        passed_item = Mock()
        passed_item.iter_markers.return_value = iter([])

        testomatio_item = self.create_mock_item_with_marker("test", "@T12345678")

        mock_session._pytestomatio_original_collected_items = [passed_item, testomatio_item]

        items = [passed_item, testomatio_item]

        plugin.pytest_collection_modifyitems(mock_session, mock_config, items)

        assert items == [testomatio_item]

    def test_item_already_in_items_not_duplicated(self, plugin, mock_session, mock_config):
        """Test that items not duplicated with other active filters"""
        mock_config.getoption.return_value = "@T12345678"
        mock_config.option.keyword = "test"

        item = self.create_mock_item_with_marker("test", "@T12345678")
        mock_session._pytestomatio_original_collected_items = [item]

        items = [item]
        plugin.pytest_collection_modifyitems(mock_session, mock_config, items)

        assert items == [item]
        assert len(items) == 1
