from typing import Optional
import boto3
import logging
from io import BytesIO
import mimetypes

log = logging.getLogger(__name__)
log.setLevel('INFO')


def parse_endpoint(endpoint: str = None) -> Optional[str]:
    if endpoint.startswith('https://'):
        return endpoint[8:]
    elif endpoint.startswith('http://'):
        return endpoint[7:]
    return endpoint

# TODO: review error handling. It should be save, and only create log entries without effecting test execution.
class S3Connector:
    def __init__(self,
                 aws_region_name: Optional[str],
                 aws_access_key_id: Optional[str],
                 aws_secret_access_key: Optional[str],
                 endpoint: Optional[str],
                 bucket_name: Optional[str],
                 bucker_prefix: Optional[str],
                 acl: Optional[str] = 'public-read'
                 ):

        self.aws_region_name = aws_region_name
        self.endpoint = parse_endpoint(endpoint)
        self.bucket_name = bucket_name
        self.bucker_prefix = bucker_prefix
        self.client = None
        self._is_logged_in = False
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.acl = acl

    def login(self):
        log.debug('creating s3 session')
        self.client = boto3.client(
            's3',
            endpoint_url=f'https://{self.endpoint}',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region_name
            )

        self._is_logged_in = True
        log.info('s3 session created')

    # TODO: upload files async
    def upload_files(self, file_list, bucket_name: str = None):
        links = []
        for file_path, key in file_list:
            link = self.upload_file(file_path=file_path, key=key, bucket_name=bucket_name)
            links.append(link)
        return [link for link in links if link is not None]


    def upload_file(self, file_path: str, key: str = None, bucket_name: str = None) -> Optional[str]:
        if not self._is_logged_in:
            log.warning('s3 session is not created, creating new one')
            return
        if not key:
            key = file_path
        key = f"{self.bucker_prefix}/{key}"
        if not bucket_name:
            bucket_name = self.bucket_name

        content_type, _ = mimetypes.guess_type(key)
        if content_type is None:
            content_type = 'application/octet-stream'

        try:
            log.info(f'uploading artifact {file_path} to s3://{bucket_name}/{key}')
            self.client.upload_file(file_path, bucket_name, key, ExtraArgs={'ACL': self.acl, 'ContentType': content_type})
            log.info(f'artifact {file_path} uploaded to s3://{bucket_name}/{key}')
            return f'https://{bucket_name}.{self.endpoint}/{key}'
        except Exception as e:
            log.error(f'failed to upload file {file_path} to s3://{bucket_name}/{key}: {e}')

    def upload_file_object(self, file_bytes: bytes, key: str, bucket_name: str = None) -> Optional[str]:
        if not self._is_logged_in:
            log.warning('s3 session is not created, creating new one')
            return
        file = BytesIO(file_bytes)
        if not bucket_name:
            bucket_name = self.bucket_name
        key = f"{self.bucker_prefix}/{key}"

        content_type, _ = mimetypes.guess_type(key)
        if content_type is None:
            content_type = 'application/octet-stream'

        try:
            log.info(f'uploading artifact {key} to s3://{bucket_name}/{key}')
            self.client.upload_fileobj(file, bucket_name, key, ExtraArgs={'ACL': self.acl, 'ContentType': content_type})
            log.info(f'artifact {key} uploaded to s3://{bucket_name}/{key}')
            return f'https://{bucket_name}.{self.endpoint}/{key}'
        except Exception as e:
            log.error(f'failed to upload file {key} to s3://{bucket_name}/{key}: {e}')
