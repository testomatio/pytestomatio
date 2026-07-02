import pytest
from pytestomatio.services.run_artifact_storage import RunArtifactStorage, run_artifact_storage


class TestRunArtifactStorage:

    @pytest.fixture
    def storage(self):
        instance = RunArtifactStorage()
        instance._paths = []
        return instance

    def test_put_stores_path(self, storage):
        storage.put('/path/to/artifact.png')

        assert storage._paths == ['/path/to/artifact.png']

    def test_put_multiple_paths_accumulates(self, storage):
        storage.put('/path/one.png')
        storage.put('/path/two.png')

        assert storage._paths == ['/path/one.png', '/path/two.png']

    def test_get_returns_stored_paths(self, storage):
        storage.put('/path/artifact.png')

        assert storage.get() == ['/path/artifact.png']

    def test_get_empty_storage(self, storage):
        assert storage.get() == []

    def test_clear_empties_storage(self, storage):
        storage.put('/path/artifact.png')

        storage.clear()

        assert storage.get() == []

    def test_clear_on_empty_storage_does_not_raise(self, storage):
        storage.clear()

    def test_get_returns_internal_list(self, storage):
        storage.put('/path/artifact.png')

        assert storage.get() is storage._paths


class TestRunArtifactStorageSingleton:

    @pytest.fixture(autouse=True)
    def cleanup(self):
        yield
        run_artifact_storage._paths.clear()

    def test_is_instance_of_RunArtifactStorage(self):
        assert isinstance(run_artifact_storage, RunArtifactStorage)

    def test_singleton_returns_same_instance(self):
        from pytestomatio.services.run_artifact_storage import run_artifact_storage as storage2

        assert run_artifact_storage is storage2

    def test_singleton_shares_state(self):
        from pytestomatio.services.run_artifact_storage import run_artifact_storage as storage2

        run_artifact_storage.put('/path/artifact.png')

        assert storage2.get() == ['/path/artifact.png']
