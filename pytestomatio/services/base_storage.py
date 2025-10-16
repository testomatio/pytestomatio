from abc import abstractmethod, ABC


class BaseStorage(ABC):

    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances.get(cls)

    def __init__(self):
        self.storage = {}

    @abstractmethod
    def get(self, identifier):
        raise NotImplemented

    @abstractmethod
    def put(self, identifier, data):
        raise NotImplemented

    @abstractmethod
    def clear(self, identifier):
        raise NotImplemented
