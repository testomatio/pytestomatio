import pytest
from unittest.mock import Mock
from _pytest.python import Function

from pytestomatio.testomatio.testomatio import Testomatio
from pytestomatio.testomatio.testRunConfig import TestRunConfig
from pytestomatio.connect.s3_connector import S3Connector


class TestTestomatio:
    """Tests for Testomatio"""

    @pytest.fixture
    def mock_test_run_config(self):
        config = Mock(spec=TestRunConfig)
        config.test_run_id = "run_12345"
        return config

    @pytest.fixture
    def mock_s3_connector(self):
        return Mock(spec=S3Connector)

    @pytest.fixture
    def testomatio_instance(self, mock_test_run_config, mock_s3_connector):
        return Testomatio(mock_test_run_config, mock_s3_connector)

    def test_init_default(self):
        """Test init with default params"""
        testomatio = Testomatio()

        assert testomatio.s3_connector is None
        assert testomatio.test_run_config is None
        assert testomatio.connector is None

    def test_init_with_parameters(self, mock_test_run_config, mock_s3_connector):
        """Test init with params"""
        testomatio = Testomatio(mock_test_run_config, mock_s3_connector)

        assert testomatio.test_run_config == mock_test_run_config
        assert testomatio.s3_connector == mock_s3_connector
        assert testomatio.connector is None

    def test_upload_files_success(self, testomatio_instance, mock_s3_connector):
        """Test successful file upload"""
        files_list = ["file1.txt", "file2.txt"]
        mock_s3_connector.upload_files.return_value = "https://s3.bucket.com/files"

        result = testomatio_instance.upload_files(files_list, "custom-bucket")

        assert result == "https://s3.bucket.com/files"
        mock_s3_connector.upload_files.assert_called_once_with(files_list, "custom-bucket")

    def test_upload_files_no_run_id(self, mock_s3_connector):
        """Test upload_files without test_run_id"""
        config = Mock()
        config.test_run_id = None

        testomatio = Testomatio(config, mock_s3_connector)

        result = testomatio.upload_files(["file.txt"])

        assert result == ""
        mock_s3_connector.upload_files.assert_not_called()

    def test_upload_file_success(self, testomatio_instance, mock_s3_connector):
        """Test successful file upload"""
        mock_s3_connector.upload_file.return_value = "https://s3.bucket.com/file.txt"

        result = testomatio_instance.upload_file("/path/to/file.txt", "custom_key", "custom-bucket")

        assert result == "https://s3.bucket.com/file.txt"
        mock_s3_connector.upload_file.assert_called_once_with("/path/to/file.txt", "custom_key", "custom-bucket")

    def test_upload_file_with_defaults(self, testomatio_instance, mock_s3_connector):
        """Test upload_file with default params"""
        mock_s3_connector.upload_file.return_value = "https://s3.bucket.com/file.txt"

        result = testomatio_instance.upload_file("/path/to/file.txt")

        mock_s3_connector.upload_file.assert_called_once_with("/path/to/file.txt", None, None)

    def test_upload_file_no_run_id(self, mock_s3_connector):
        """Test upload_file without test_run_id"""
        config = Mock()
        config.test_run_id = None

        testomatio = Testomatio(config, mock_s3_connector)

        result = testomatio.upload_file("/path/to/file.txt")

        assert result == ""
        mock_s3_connector.upload_file.assert_not_called()

    def test_upload_file_object_success(self, testomatio_instance, mock_s3_connector):
        """Test successful file object upload"""
        file_bytes = b"test file content"
        mock_s3_connector.upload_file_object.return_value = "https://s3.bucket.com/object.bin"

        result = testomatio_instance.upload_file_object(file_bytes, "object_key", "custom-bucket")

        assert result == "https://s3.bucket.com/object.bin"
        mock_s3_connector.upload_file_object.assert_called_once_with(file_bytes, "object_key", "custom-bucket")

    def test_upload_file_object_with_defaults(self, testomatio_instance, mock_s3_connector):
        """Test upload_file_object in default bucket"""
        file_bytes = b"test content"
        mock_s3_connector.upload_file_object.return_value = "https://s3.bucket.com/object.bin"

        result = testomatio_instance.upload_file_object(file_bytes, "object_key")

        mock_s3_connector.upload_file_object.assert_called_once_with(file_bytes, "object_key", None)

    def test_upload_file_object_no_run_id(self, mock_s3_connector):
        """Test upload_file_object without test_run_id"""
        config = Mock()
        config.test_run_id = None

        testomatio = Testomatio(config, mock_s3_connector)

        result = testomatio.upload_file_object(b"content", "key")

        assert result == ""
        mock_s3_connector.upload_file_object.assert_not_called()

    def test_add_artifacts_new_stash(self, testomatio_instance):
        """Test add artifacts to new stash"""
        mock_node = Mock(spec=Function)
        mock_node.stash = {}

        url_list = ["https://s3.com/file1.png", "https://s3.com/file2.png"]

        testomatio_instance.add_artifacts(mock_node, url_list)

        assert mock_node.stash["artifact_urls"] == url_list

    def test_add_artifacts_existing_stash(self, testomatio_instance):
        """Test add artifacts to existing stash"""
        mock_node = Mock(spec=Function)
        mock_node.stash = {"artifact_urls": ["https://s3.com/existing.png"]}

        url_list = ["https://s3.com/new1.png", "https://s3.com/new2.png"]

        testomatio_instance.add_artifacts(mock_node, url_list)

        expected = ["https://s3.com/existing.png", "https://s3.com/new1.png", "https://s3.com/new2.png"]
        assert mock_node.stash["artifact_urls"] == expected

    def test_add_artifacts_filters_none_values(self, testomatio_instance):
        """Test None filtration"""
        mock_node = Mock(spec=Function)
        mock_node.stash = {}

        url_list = ["https://s3.com/file1.png", None, "https://s3.com/file2.png", None]

        testomatio_instance.add_artifacts(mock_node, url_list)

        expected = ["https://s3.com/file1.png", "https://s3.com/file2.png"]
        assert mock_node.stash["artifact_urls"] == expected

