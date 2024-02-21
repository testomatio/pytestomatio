from _pytest.python import Function
from .s3_connector import S3Connector

class Testomatio:
    def __init__(self) -> None:
        self.s3_connector = None
        pass

    def set_s3_connector(self, s3_connector: S3Connector) -> None:
        self.s3_connector = s3_connector

    def upload_file(self, file_path: str, key: str = None, bucket_name: str = None) -> str:
        return self.s3_connector.upload_file(file_path, key, bucket_name)

    def upload_file_object(self, file_bytes: bytes, key: str, bucket_name: str = None) -> str:
        return self.s3_connector.upload_file_object(file_bytes, key, bucket_name)

    def add_artifacts(self, node: Function, urls: list[str]) -> None:
        artifact_urls = node.stash.get("artifact_urls", [])
        artifact_urls.extend(urls)
        node.stash["artifact_urls"] = artifact_urls
