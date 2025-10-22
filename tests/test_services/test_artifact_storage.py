import pytest
from pytestomatio.services.artifact_storage import ArtifactStorage, artifact_storage


class TestArtifactStorage:
    """Tests for ArtifactStorage"""

    @pytest.fixture
    def storage(self):
        """Creates new ArtifactStorage for every test"""
        instance = ArtifactStorage()
        instance.storage = {}
        return instance

    def test_put_new_artifact(self, storage):
        """Test adding new artifact for test_id"""
        test_id = "test_123"
        data = 'artifact1'

        storage.put(test_id, data)

        assert test_id in storage.storage
        assert len(storage.storage[test_id]) == 1
        assert storage.storage[test_id][0] == data

    def test_put_multiple_artifacts_same_test(self, storage):
        """Test adding multiple artifacts for one test_id"""
        test_id = "test_456"
        data1 = 'artifact1'
        data2 = 'artifact2'

        storage.put(test_id, data1)
        storage.put(test_id, data2)

        assert len(storage.storage[test_id]) == 2
        assert storage.storage[test_id][0] == data1
        assert storage.storage[test_id][1] == data2

    def test_put_different_test_ids(self, storage):
        """Test artifacts adding for different test_id"""
        test_id1 = "test_1"
        test_id2 = "test_2"
        data1 = 'artifact1'
        data2 = "artifact2"

        storage.put(test_id1, data1)
        storage.put(test_id2, data2)

        assert len(storage.storage) == 2
        assert storage.storage[test_id1] == [data1]
        assert storage.storage[test_id2] == [data2]

    def test_get_existing_artifacts(self, storage):
        """Test get existed artifacts"""
        test_id = "test_789"
        data = 'artifact1'
        storage.put(test_id, data)

        result = storage.get(test_id)

        assert result == [data]
        assert len(result) == 1

    def test_get_non_existing_test_id(self, storage):
        """Test artifacts get for non existent test_id"""
        result = storage.get("non_existing_id")

        assert result == []
        assert isinstance(result, list)

    def test_get_empty_storage(self, storage):
        """Test get from empty storage"""
        result = storage.get("any_id")

        assert result == []

    def test_clear_existing_test_id(self, storage):
        """Test clear existing test_id"""
        test_id = "test_clear"
        data = "test.log"
        storage.put(test_id, data)

        storage.clear(test_id)

        assert test_id not in storage.storage
        assert storage.get(test_id) == []

    def test_clear_non_existing_test_id(self, storage):
        """Test clearing non existent test_id not raises error"""
        storage.clear("non_existing_id")

    def test_clear_does_not_affect_other_tests(self, storage):
        """Test clear() not affects other test_id"""
        test_id1 = "test_1"
        test_id2 = "test_2"
        data1 = 'path1'
        data2 = 'path2'

        storage.put(test_id1, data1)
        storage.put(test_id2, data2)
        storage.clear(test_id1)

        assert test_id1 not in storage.storage
        assert storage.get(test_id2) == [data2]

    def test_put_empty_data(self, storage):
        """Test adding empty data"""
        test_id = "test_empty"
        storage.put(test_id, '')

        assert storage.get(test_id) == ['']

    def test_multiple_operations_sequence(self, storage):
        """Test put, get, clear operation sequence"""
        test_id = "test_sequence"
        data1 = 'path1'
        data2 = 'path2'

        storage.put(test_id, data1)
        assert len(storage.get(test_id)) == 1

        storage.put(test_id, data2)
        assert len(storage.get(test_id)) == 2

        storage.clear(test_id)
        assert storage.get(test_id) == []


class TestArtifactStorageSingleton:
    """Tests for global artifact_storage"""

    def test_artifact_storage_is_instance_of_ArtifactStorage(self):
        """Test artifact_storage is ArtifactStorage instance"""
        assert isinstance(artifact_storage, ArtifactStorage)

    def test_artifact_storage_singleton(self):
        """Test artifact_storage works as singleton"""
        from pytestomatio.services.artifact_storage import artifact_storage as storage2

        assert artifact_storage is storage2

    @pytest.fixture(autouse=True)
    def cleanup_global_storage(self):
        """Clears global storage after every test"""
        yield
        artifact_storage.storage.clear()
