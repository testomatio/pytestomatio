from _pytest.python import Function
from .testRunConfig import TestRunConfig
from pytestomatio.connect.s3_connector import S3Connector
from pytestomatio.connect.connector import Connector
import logging

log = logging.getLogger(__name__)


class Testomatio:
    def __init__(self, test_run_config: TestRunConfig = None,
                 s3_connector: S3Connector = None) -> None:
        self.s3_connector: S3Connector or None = s3_connector
        self.test_run_config: TestRunConfig or None = test_run_config
        self.connector: Connector or None = None

    def upload_files(self, files_list, bucket_name: str = None) -> str:
        if self.test_run_config.test_run_id is None:
            log.debug("Skipping file upload when testomatio test run is not created")
            return ""
        return self.s3_connector.upload_files(files_list, bucket_name)
    
    def upload_file(self, file_path: str, key: str = None, bucket_name: str = None) -> str:
        if self.test_run_config.test_run_id is None:
            log.debug("Skipping file upload when testomatio test run is not created")
            return ""
        return self.s3_connector.upload_file(file_path, key, bucket_name)

    def upload_file_object(self, file_bytes: bytes, key: str, bucket_name: str = None) -> str:
        if self.test_run_config.test_run_id is None:
            log.debug("Skipping file upload when testomatio test run is not created")
            return ""
        return self.s3_connector.upload_file_object(file_bytes, key, bucket_name)

    def add_artifacts(self, *args) -> None:
        urls = None
        for arg in args:
            if isinstance(arg, list):
                urls = arg
        if not urls:
            log.warn("Failed to add artifacts. No valid list of url has been provided")
            return

        if not hasattr(self, "request"):
            log.warn("Couldn't attach link to the test. Make sure pytestomatio is configured correctly.")
            return
        
        artifact_urls = self.request.node.stash.get("artifact_urls", [])
        artifact_urls.extend(urls)
        self.request.node.stash["artifact_urls"] = [ url for url in artifact_urls if url is not None]
