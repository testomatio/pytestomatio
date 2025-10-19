import pytest
from unittest.mock import Mock, patch, call
from io import BytesIO

from pytestomatio.connect.s3_connector import S3Connector, parse_endpoint


class TestParseEndpoint:
    """Tests for parse_endpoint function"""

    def test_parse_endpoint_https(self):
        """Test parsing HTTPS endpoint"""
        result = parse_endpoint("https://s3.amazonaws.com")
        assert result == "s3.amazonaws.com"

    def test_parse_endpoint_http(self):
        """Test parsing HTTP endpoint"""
        result = parse_endpoint("http://localhost:9000")
        assert result == "localhost:9000"

    def test_parse_endpoint_no_protocol(self):
        """Test parsing endpoint without"""
        result = parse_endpoint("s3.amazonaws.com")
        assert result == "s3.amazonaws.com"


class TestS3Connector:
    """Tests for S3Connector"""

    @pytest.fixture
    def s3_connector(self):
        return S3Connector(
            aws_region_name="us-east-1",
            aws_access_key_id="test_access_key",
            aws_secret_access_key="test_secret_key",
            endpoint="https://s3.amazonaws.com",
            bucket_name="test-bucket",
            bucker_prefix="test-prefix",
            acl="public-read"
        )

    def test_init(self, s3_connector):
        """Test init S3Connector"""
        assert s3_connector.aws_region_name == "us-east-1"
        assert s3_connector.aws_access_key_id == "test_access_key"
        assert s3_connector.aws_secret_access_key == "test_secret_key"
        assert s3_connector.endpoint == "s3.amazonaws.com"
        assert s3_connector.bucket_name == "test-bucket"
        assert s3_connector.bucker_prefix == "test-prefix"
        assert s3_connector.acl == "public-read"
        assert s3_connector.client is None
        assert s3_connector._is_logged_in is False

    def test_init_default_acl(self):
        """Тест ініціалізації з default ACL"""
        connector = S3Connector(None, None, None, '', None, None)
        assert connector.acl == "public-read"

    @patch('boto3.client')
    def test_login_success(self, mock_boto_client, s3_connector):
        """Test successful login"""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        s3_connector.login()

        mock_boto_client.assert_called_once_with(
            's3',
            endpoint_url='https://s3.amazonaws.com',
            aws_access_key_id='test_access_key',
            aws_secret_access_key='test_secret_key',
            region_name='us-east-1'
        )

        assert s3_connector.client is mock_client
        assert s3_connector._is_logged_in is True

    def test_upload_file_not_logged_in(self, s3_connector):
        """Test upload_file when not logged in"""
        result = s3_connector.upload_file("test.txt", "test_key")

        assert result is None

    @patch('mimetypes.guess_type')
    def test_upload_file_success(self, mock_guess_type, s3_connector):
        """Test successful file upload"""
        s3_connector._is_logged_in = True
        s3_connector.client = Mock()
        mock_guess_type.return_value = ('text/plain', None)

        result = s3_connector.upload_file("test.txt", "test_key")

        s3_connector.client.upload_file.assert_called_once_with(
            "test.txt",
            "test-bucket",
            "test-prefix/test_key",
            ExtraArgs={
                'ACL': 'public-read',
                'ContentType': 'text/plain',
                'ContentDisposition': 'inline'
            }
        )

        expected_url = "https://test-bucket.s3.amazonaws.com/test-prefix/test_key"
        assert result == expected_url

    @patch('mimetypes.guess_type')
    def test_upload_file_with_custom_bucket(self, mock_guess_type, s3_connector):
        """Test upload with custom bucket"""
        s3_connector._is_logged_in = True
        s3_connector.client = Mock()
        mock_guess_type.return_value = ('image/png', None)

        result = s3_connector.upload_file("image.png", "img_key", "custom-bucket")

        s3_connector.client.upload_file.assert_called_once_with(
            "image.png",
            "custom-bucket",
            "test-prefix/img_key",
            ExtraArgs={
                'ACL': 'public-read',
                'ContentType': 'image/png',
                'ContentDisposition': 'inline'
            }
        )

    @patch('mimetypes.guess_type')
    def test_upload_file_unknown_content_type(self, mock_guess_type, s3_connector):
        """Test with unknown content type"""
        s3_connector._is_logged_in = True
        s3_connector.client = Mock()
        mock_guess_type.return_value = (None, None)

        s3_connector.upload_file("unknown.dat", "key")

        call_args = s3_connector.client.upload_file.call_args
        assert call_args[1]['ExtraArgs']['ContentType'] == 'application/octet-stream'

    def test_upload_file_no_key_uses_filepath(self, s3_connector):
        """Test fil_path used when no key"""
        s3_connector._is_logged_in = True
        s3_connector.client = Mock()

        with patch('mimetypes.guess_type', return_value=('text/plain', None)):
            s3_connector.upload_file("path/to/file.txt")

            call_args = s3_connector.client.upload_file.call_args
            assert call_args[0][2] == "test-prefix/file.txt"

    def test_upload_file_exception_handling(self, s3_connector):
        """Test exception handling"""
        s3_connector._is_logged_in = True
        s3_connector.client = Mock()
        s3_connector.client.upload_file.side_effect = Exception("S3 Error")

        with patch('mimetypes.guess_type', return_value=('text/plain', None)):
            result = s3_connector.upload_file("test.txt", "key")

            assert result is None

    def test_upload_file_object_not_logged_in(self, s3_connector):
        """Test upload_file_object when no logged in"""
        result = s3_connector.upload_file_object(b"test data", "key")
        assert result is None

    @patch('mimetypes.guess_type')
    def test_upload_file_object_success(self, mock_guess_type, s3_connector):
        """Test successful file object upload"""
        s3_connector._is_logged_in = True
        s3_connector.client = Mock()
        mock_guess_type.return_value = ('application/json', None)

        file_bytes = b'{"test": "data"}'

        result = s3_connector.upload_file_object(file_bytes, "data.json")

        call_args = s3_connector.client.upload_fileobj.call_args

        file_obj = call_args[0][0]
        assert isinstance(file_obj, BytesIO)
        assert file_obj.read() == file_bytes
        file_obj.seek(0)

        assert call_args[0][1] == "test-bucket"
        assert call_args[0][2] == "test-prefix/data.json"

        extra_args = call_args[1]['ExtraArgs']
        assert extra_args['ContentType'] == 'application/json'
        assert extra_args['ACL'] == 'public-read'

        expected_url = "https://test-bucket.s3.amazonaws.com/test-prefix/data.json"
        assert result == expected_url

    def test_upload_file_object_custom_bucket(self, s3_connector):
        """Тест upload_file_object з кастомним bucket"""
        s3_connector._is_logged_in = True
        s3_connector.client = Mock()

        with patch('mimetypes.guess_type', return_value=('text/plain', None)):
            s3_connector.upload_file_object(b"data", "key", "custom-bucket")

            call_args = s3_connector.client.upload_fileobj.call_args
            assert call_args[0][1] == "custom-bucket"

    def test_upload_file_object_exception_handling(self, s3_connector):
        """Test exception handling"""
        s3_connector._is_logged_in = True
        s3_connector.client = Mock()
        s3_connector.client.upload_fileobj.side_effect = Exception("Upload failed")

        with patch('mimetypes.guess_type', return_value=('text/plain', None)):
            result = s3_connector.upload_file_object(b"data", "key")

            assert result is None

    def test_upload_files_success(self, s3_connector):
        """Test upload_files with multiple files"""
        s3_connector._is_logged_in = True

        with patch.object(s3_connector, 'upload_file') as mock_upload:
            mock_upload.side_effect = [
                "https://bucket.s3.com/file1.txt",
                "https://bucket.s3.com/file2.txt",
                None
            ]

            file_list = [
                ("file1.txt", "key1"),
                ("file2.txt", "key2"),
                ("file3.txt", "key3")
            ]

            result = s3_connector.upload_files(file_list, "custom-bucket")

            expected_calls = [
                call(file_path="file1.txt", key="key1", bucket_name="custom-bucket"),
                call(file_path="file2.txt", key="key2", bucket_name="custom-bucket"),
                call(file_path="file3.txt", key="key3", bucket_name="custom-bucket")
            ]
            mock_upload.assert_has_calls(expected_calls)

            assert result == [
                "https://bucket.s3.com/file1.txt",
                "https://bucket.s3.com/file2.txt"
            ]

    def test_upload_files_empty_list(self, s3_connector):
        """Test upload_files with empty list"""
        result = s3_connector.upload_files([])
        assert result == []

    def test_private_acl_configuration(self):
        """Test config with private ACL"""
        connector = S3Connector(
            aws_region_name="us-west-2",
            aws_access_key_id="key",
            aws_secret_access_key="secret",
            endpoint="https://s3.amazonaws.com",
            bucket_name="bucket",
            bucker_prefix="prefix",
            acl="private"
        )

        connector._is_logged_in = True
        connector.client = Mock()

        with patch('mimetypes.guess_type', return_value=('text/plain', None)):
            connector.upload_file("test.txt", "key")

            call_args = connector.client.upload_file.call_args
            assert call_args[1]['ExtraArgs']['ACL'] == 'private'
