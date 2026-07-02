class RunArtifactStorage:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._paths = []
        return cls._instance

    def put(self, path: str):
        if path not in self._paths:
            self._paths.append(path)

    def get(self) -> list:
        return self._paths

    def clear(self):
        self._paths.clear()


run_artifact_storage = RunArtifactStorage()
