import boto3
import logging
from io import BytesIO

log = logging.getLogger(__name__)
log.setLevel('INFO')


class S3Connector:
    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str,
                 endpoint: str, bucket_name: str = None):
        if endpoint.startswith('https://'):
            self.endpoint = endpoint[8:]
        elif endpoint.startswith('http://'):
            self.endpoint = endpoint[7:]
        else:
            self.endpoint = endpoint
        self.bucket_name = bucket_name
        self.client = None
        self._is_logged_in = False
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key

    def login(self):
        log.debug('creating s3 session')
        self.client = boto3.client(
            's3',
            endpoint_url=f'https://{self.endpoint}',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key)
        self._is_logged_in = True
        log.info('s3 session created')

    def upload_file(self, file_path: str, key: str = None, bucket_name: str = None) -> str or None:
        if not self._is_logged_in:
            log.warning('s3 session is not created, creating new one')
            return
        if not key:
            key = file_path
        if not bucket_name:
            bucket_name = self.bucket_name
        if bucket_name is None:
            raise Exception('bucket name is not defined')
        log.info(f'uploading artifact {file_path} to s3://{bucket_name}/{key}')
        self.client.upload_file(file_path, bucket_name, key)
        log.info(f'artifact {file_path} uploaded to s3://{bucket_name}/{key}')
        return f'https://{bucket_name}.{self.endpoint}/{key}'

    def upload_file_object(self, file_bytes: bytes, key: str, bucket_name: str = None) -> str or None:
        if not self._is_logged_in:
            log.warning('s3 session is not created, creating new one')
            return
        file = BytesIO(file_bytes)
        if not bucket_name:
            bucket_name = self.bucket_name
        if bucket_name is None:
            raise Exception('bucket name is not defined')
        log.info(f'uploading artifact {key} to s3://{bucket_name}/{key}')
        self.client.upload_fileobj(file, bucket_name, key)
        log.info(f'artifact {key} uploaded to s3://{bucket_name}/{key}')
        return f'https://{bucket_name}.{self.endpoint}/{key}'
