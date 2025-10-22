import pytest
from pytestomatio.services.meta_storage import MetaStorage, meta_storage


class TestMetaStorage:
    """Tests for MetaStorage"""

    @pytest.fixture
    def storage(self):
        """Creates new MetaStorage for every test"""
        instance = MetaStorage()
        instance.storage = {}
        return instance

    def test_put_new_metadata(self, storage):
        """Test adding new metadata test_id"""
        test_id = "test_123"
        data = {"status": "passed", "duration": 1.5}

        storage.put(test_id, data)

        assert test_id in storage.storage
        assert storage.storage[test_id] == data

    def test_put_updates_existing_metadata(self, storage):
        """Test update existing metadata"""
        test_id = "test_456"
        initial_data = {"status": "running", "start_time": "10:00"}
        update_data = {"status": "passed", "end_time": "10:05"}

        storage.put(test_id, initial_data)
        storage.put(test_id, update_data)

        result = storage.get(test_id)
        assert result["status"] == "passed"
        assert result["start_time"] == "10:00"
        assert result["end_time"] == "10:05"

    def test_put_overwrites_existing_keys(self, storage):
        """Test overwrites existing keys"""
        test_id = "test_overwrite"
        storage.put(test_id, {"status": "running", "attempt": 1})
        storage.put(test_id, {"status": "failed", "attempt": 2})

        result = storage.get(test_id)
        assert result["status"] == "failed"
        assert result["attempt"] == 2

    def test_put_different_test_ids(self, storage):
        """Test get metadata for different test_id"""
        test_id1 = "test_1"
        test_id2 = "test_2"
        data1 = {"result": "pass"}
        data2 = {"result": "fail"}

        storage.put(test_id1, data1)
        storage.put(test_id2, data2)

        assert len(storage.storage) == 2
        assert storage.storage[test_id1] == data1
        assert storage.storage[test_id2] == data2

    def test_get_existing_metadata(self, storage):
        """Test get existing metadata"""
        test_id = "test_789"
        data = {"duration": 2.5, "retries": 0}
        storage.put(test_id, data)

        result = storage.get(test_id)

        assert result == data

    def test_get_non_existing_test_id(self, storage):
        """Test get metadata for non existent test_id"""
        result = storage.get("non_existing_id")

        assert result == {}
        assert isinstance(result, dict)

    def test_get_empty_storage(self, storage):
        """Test get data from empty storage"""
        result = storage.get("any_id")

        assert result == {}

    def test_clear_existing_test_id(self, storage):
        """Test clearing existing test_id"""
        test_id = "test_clear"
        data = {"status": "completed"}
        storage.put(test_id, data)

        storage.clear(test_id)

        assert test_id not in storage.storage
        assert storage.get(test_id) == {}

    def test_clear_non_existing_test_id(self, storage):
        """Test clearing not existent test_id not raising error"""
        storage.clear("non_existing_id")

    def test_clear_does_not_affect_other_tests(self, storage):
        """Test clear() not affects other test_id"""
        test_id1 = "test_1"
        test_id2 = "test_2"
        data1 = {"meta": "data1"}
        data2 = {"meta": "data2"}

        storage.put(test_id1, data1)
        storage.put(test_id2, data2)
        storage.clear(test_id1)

        assert test_id1 not in storage.storage
        assert storage.get(test_id2) == data2

    def test_put_empty_dict(self, storage):
        """Test adding empty dict"""
        test_id = "test_empty"
        storage.put(test_id, {})

        assert storage.get(test_id) == {}

    def test_put_with_various_data_types(self, storage):
        """Test adding metadata with different types"""
        test_id = "test_types"
        data = {
            "string": "value",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "none": None
        }

        storage.put(test_id, data)

        assert storage.get(test_id) == data

    def test_multiple_operations_sequence(self, storage):
        """Test put, get, clear operations sequence"""
        test_id = "test_sequence"
        data1 = {"step": 1}
        data2 = {"step": 2, "status": "running"}

        storage.put(test_id, data1)
        assert storage.get(test_id) == {"step": 1}

        storage.put(test_id, data2)
        assert storage.get(test_id) == {"step": 2, "status": "running"}

        storage.clear(test_id)
        assert storage.get(test_id) == {}

    def test_put_incremental_updates(self, storage):
        """Test incremental updates"""
        test_id = "test_incremental"

        storage.put(test_id, {"field1": "value1"})
        storage.put(test_id, {"field2": "value2"})
        storage.put(test_id, {"field3": "value3"})
        storage.put(test_id, {"field1": "updated_value1"})

        result = storage.get(test_id)
        assert result == {
            "field1": "updated_value1",
            "field2": "value2",
            "field3": "value3"
        }

    def test_put_preserves_unmodified_fields(self, storage):
        """Test put preserver unmodified fields on update"""
        test_id = "test_preserve"
        storage.put(test_id, {
            "name": "Test Case",
            "status": "pending",
            "priority": "high",
            "tags": ["smoke"]
        })

        storage.put(test_id, {"status": "running"})

        result = storage.get(test_id)
        assert result["name"] == "Test Case"
        assert result["status"] == "running"
        assert result["priority"] == "high"
        assert result["tags"] == ["smoke"]


class TestMetaStorageSingleton:
    """Tests for global meta_storage"""

    def test_meta_storage_is_instance_of_MetaStorage(self):
        """Test meta_storage is MetaStorage instance"""
        assert isinstance(meta_storage, MetaStorage)

    def test_meta_storage_singleton(self):
        """Test meta_storage is singleton"""
        from pytestomatio.services.meta_storage import meta_storage as storage2

        assert meta_storage is storage2

    @pytest.fixture(autouse=True)
    def cleanup_global_storage(self):
        """Clears global storage after every test"""
        yield
        meta_storage.storage.clear()

