

class LinkStorage:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.storage = {}

    def put(self, test_id, data: dict):
        existing_data = self.get(test_id)
        if existing_data:
            existing_data.append(data)
            return
        self.storage.update({test_id: [data]})

    def get(self, test_id):
        return self.storage.get(test_id, [])

    def clear(self, test_id):
        self.storage.pop(test_id, None)


link_storage = LinkStorage()
