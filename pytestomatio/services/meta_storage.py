from pytestomatio.services.base_storage import BaseStorage


class MetaStorage(BaseStorage):

    def put(self, test_id, data: dict):
        existing_data = self.get(test_id)
        if existing_data:
            existing_data.update(data)
            data = existing_data
        self.storage.update({test_id: data})

    def get(self, test_id):
        return self.storage.get(test_id, {})

    def clear(self, test_id):
        self.storage.pop(test_id, None)


meta_storage = MetaStorage()

