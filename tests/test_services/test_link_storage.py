import pytest
from pytestomatio.services.link_storage import LinkStorage, link_storage


class TestLinkStorage:
    """Tests for LinkStorage"""

    @pytest.fixture
    def storage(self):
        """Creates new LinkStorage for every test"""
        instance = LinkStorage()
        instance.storage = {}
        return instance

    def test_put_new_link(self, storage):
        """Тest adding new link for test_id"""
        test_id = "test_123"
        data = {"label": "Example Link"}

        storage.put(test_id, data)

        assert test_id in storage.storage
        assert len(storage.storage[test_id]) == 1
        assert storage.storage[test_id][0] == data

    def test_put_multiple_links_same_test(self, storage):
        """Test adding multiple links for one test_id"""
        test_id = "test_456"
        data1 = {"label": "Link 1"}
        data2 = {"label": "Link 2"}

        storage.put(test_id, data1)
        storage.put(test_id, data2)

        assert len(storage.storage[test_id]) == 2
        assert storage.storage[test_id][0] == data1
        assert storage.storage[test_id][1] == data2

    def test_put_different_test_ids(self, storage):
        """Test link add for different test_id"""
        test_id1 = "test_1"
        test_id2 = "test_2"
        data1 = {"label": "Test 1 link"}
        data2 = {"label": "Test 2 link"}

        storage.put(test_id1, data1)
        storage.put(test_id2, data2)

        assert len(storage.storage) == 2
        assert storage.storage[test_id1] == [data1]
        assert storage.storage[test_id2] == [data2]

    def test_get_existing_links(self, storage):
        """Test get existing links"""
        test_id = "test_789"
        data = {"label": "documentation"}
        storage.put(test_id, data)

        result = storage.get(test_id)

        assert result == [data]
        assert len(result) == 1

    def test_get_non_existing_test_id(self, storage):
        """Test get links for non existent test_id"""
        result = storage.get("non_existing_id")

        assert result == []
        assert isinstance(result, list)

    def test_get_empty_storage(self, storage):
        """Test get data from empty storage"""
        result = storage.get("any_id")

        assert result == []

    def test_clear_existing_test_id(self, storage):
        """Test clear existing test_id"""
        test_id = "test_clear"
        data = {"label": "test"}
        storage.put(test_id, data)

        storage.clear(test_id)

        assert test_id not in storage.storage
        assert storage.get(test_id) == []

    def test_clear_non_existing_test_id(self, storage):
        """Test clearing not existent test_id not raising error"""
        storage.clear("non_existing_id")

    def test_clear_does_not_affect_other_tests(self, storage):
        """Test clear() not affects other test_id"""
        test_id1 = "test_1"
        test_id2 = "test_2"
        data1 = {"label": "l1"}
        data2 = {"label": "l2"}

        storage.put(test_id1, data1)
        storage.put(test_id2, data2)
        storage.clear(test_id1)

        assert test_id1 not in storage.storage
        assert storage.get(test_id2) == [data2]

    def test_put_empty_dict(self, storage):
        """Test adding empty dict"""
        test_id = "test_empty"
        storage.put(test_id, {})

        assert storage.get(test_id) == [{}]

    def test_put_multiple_link_types(self, storage):
        """Test adding different link types for one test"""
        test_id = "test_multi_type"
        label = {"label": "l1"}
        test = {"test": "R342eRe"}
        jira = {"jira": "PROJ-1"}

        storage.put(test_id, label)
        storage.put(test_id, test)
        storage.put(test_id, jira)

        links = storage.get(test_id)
        assert len(links) == 3
        assert label in links
        assert test in links
        assert jira in links

    def test_multiple_operations_sequence(self, storage):
        """Test put, get, clear operation sequence"""
        test_id = "test_sequence"
        data1 = {"label": "l1"}
        data2 = {"label": "l2"}

        storage.put(test_id, data1)
        assert len(storage.get(test_id)) == 1

        storage.put(test_id, data2)
        assert len(storage.get(test_id)) == 2

        storage.clear(test_id)
        assert storage.get(test_id) == []


class TestLinkStorageSingleton:
    """Tests for global link_storage"""

    def test_link_storage_is_instance_of_LinkStorage(self):
        """Test link_storage is LinkStorage instance"""
        assert isinstance(link_storage, LinkStorage)

    def test_link_storage_singleton(self):
        """Test link_storage works as singleton"""
        from pytestomatio.services.link_storage import link_storage as storage2

        assert link_storage is storage2

    @pytest.fixture(autouse=True)
    def cleanup_global_storage(self):
        """Clears global storage after every test"""
        yield
        link_storage.storage.clear()
