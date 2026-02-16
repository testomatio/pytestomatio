import os

import requests
from requests.exceptions import HTTPError, ConnectionError
import logging
from os.path import join, normpath
from os import getenv

from pytestomatio.connect.exception import MaxRetriesException
from pytestomatio.utils.helper import safe_string_list
from pytestomatio.testing.testItem import TestItem
import time

log = logging.getLogger('pytestomatio')
MAX_RETRIES_DEFAULT = 5
RETRY_INTERVAL_DEFAULT = 5


class Connector:
    def __init__(self, base_url: str = '', api_key: str = None):
        max_retries = os.environ.get('TESTOMATIO_MAX_REQUEST_FAILURES', '')
        retry_interval = os.environ.get('TESTOMATIO_REQUEST_INTERVAL', '')
        self.base_url = base_url
        self._session = requests.Session()
        self.jwt: str = ''
        self.api_key = api_key
        self.max_retries = int(max_retries) if max_retries.isdigit() else MAX_RETRIES_DEFAULT
        self.retry_interval = int(retry_interval) if retry_interval.isdigit() else RETRY_INTERVAL_DEFAULT

    @property
    def session(self):
        """Get the session, creating it and applying proxy settings if necessary."""
        self._apply_proxy_settings()
        return self._session

    @session.setter
    def session(self, value):
        """Allow setting a custom session, while still applying proxy settings."""
        self._session = value
        self._apply_proxy_settings()

    def _apply_proxy_settings(self):
        """Apply proxy settings based on environment variables, fallback to no proxy if unavailable."""
        http_proxy = getenv("HTTP_PROXY")
        log.debug(f"HTTP_PROXY: {http_proxy}")
        if http_proxy:
            self._session.proxies = {"http": http_proxy, "https": http_proxy}
            self._session.verify = False
            log.debug(f"Proxy settings applied: {self._session.proxies}")

            if not self._test_proxy_connection(timeout=1):
                log.debug("Proxy is unavailable. Falling back to a direct connection.")
                self._session.proxies.clear()
                self._session.verify = True
        else:
            log.debug("No proxy settings found. Using a direct connection.")
            self._session.proxies.clear()
            self._session.verify = True
            self._test_proxy_connection()

    def _test_proxy_connection(self, test_url="https://api.ipify.org?format=json", timeout=30, retry_interval=1):
        log.debug("Current session: %s", self._session.proxies)
        log.debug("Current verify: %s", self._session.verify)

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self._session.get(test_url, timeout=5)
                response.raise_for_status()
                log.debug("Internet connection is available.")
                return True
            except requests.exceptions.RequestException as e:
                log.error("Internet connection is unavailable. Error: %s", e)
                time.sleep(retry_interval)
        
        log.error("Internet connection check timed out after %d seconds.", timeout)
        return False

    def _should_retry(self, response: requests.Response) -> bool:
        """Checks if request should be retried.
        Skipped status codes explanation:
         400 - Bad request(probably wrong API key)
         404 - Resource not found. No point to retry request.
         429 - Limit exceeded
         500 - Internal server error
        """
        if response.status_code in (400, 404, 429, 500):
            return False
        return response.status_code >= 401

    def _send_request_with_retry(self, method: str, url: str, **kwargs):
        """Send HTTP request with retry logic"""
        for attempt in range(self.max_retries):
            log.debug(f'Trying to send request to {self.base_url}. Attempt {attempt+1}/{self.max_retries}')
            try:
                request_func = getattr(self.session, method)
                response = request_func(url, **kwargs)

                if self._should_retry(response):
                    if attempt < self.max_retries:
                        log.error(f'Request attempt failed. Response code: {response.status_code}. '
                                  f'Retrying in {self.retry_interval} seconds')
                        time.sleep(self.retry_interval)
                        continue

                return response
            except ConnectionError as ce:
                log.error(f'Failed to connect to {self.base_url}: {ce}')
                raise
            except HTTPError as he:
                log.error(f'HTTP error occurred while connecting to {self.base_url}: {he}')
                raise
            except Exception as e:
                log.error(f'An unexpected exception occurred. Please report an issue: {e}')
                raise

        log.error(f'Retries attempts exceeded.')
        raise MaxRetriesException()

    def load_tests(
            self,
            tests: list[TestItem],
            no_empty: bool = False,
            no_detach: bool = False,
            structure: bool = False,
            create: bool = False,
            directory: str = None
    ):
        url = f'{self.base_url}/api/load?api_key={self.api_key}'
        request = {
            "framework": "pytest",
            "language": "python",
            "noempty": no_empty,
            "no-detach": no_detach,
            "structure": structure if not no_empty else False,
            "create": create,
            "sync": True,
            "tests": []
        }
        for test in tests:
            request['tests'].append({
                "name": test.sync_title,
                "suites": [
                    test.class_name
                ],
                "code": test.source_code,
                "description": test.docstring,
                "file": test.file_path if structure else (
                    test.file_name if directory is None else normpath(join(directory, test.file_name))),
                "labels": safe_string_list(getenv('TESTOMATIO_SYNC_LABELS')),
            })

        log.info(f'Starting tests loading to {self.base_url}')
        try:
            response = self._send_request_with_retry('post', url, json=request)
        except Exception as e:
            log.error(f'Failed to load tests to {self.base_url}')
            return

        if response.status_code < 400:
            log.info(f'Tests loaded to {self.base_url}')
        else:
            log.error(f'Failed to load tests to {self.base_url}. Status code: {response.status_code}')

    def get_tests(self, test_metadata: list[TestItem]) -> dict:
        log.info('Trying to receive test ids from testomat.io')
        url = f'{self.base_url}/api/test_data?api_key={self.api_key}'
        try:
            response = self._send_request_with_retry('get', url)
            if response.status_code < 400:
                log.info('Test ids received')
                return response.json()
            else:
                log.error('Failed to get test ids from testomat.io')
        except Exception as e:
            log.error('Failed to get test ids from testomat.io')


    def create_test_run(self, access_event: str, title: str, group_title, env: str, label: str, shared_run: bool, shared_run_timeout: str,
                        parallel, ci_build_url: str) -> dict | None:
        request = {
            "access_event": access_event,
            "api_key": self.api_key,
            "title": title,
            "group_title": group_title,
            "env": env,
            "label": label,
            "parallel": parallel,
            "ci_build_url": ci_build_url,
            "shared_run": shared_run,
            "shared_run_timeout": shared_run_timeout,
        }
        filtered_request = {k: v for k, v in request.items() if v is not None}
        url = f'{self.base_url}/api/reporter'
        log.info('Creating test run')
        try:
            response = self._send_request_with_retry('post', url, json=filtered_request)
        except Exception as e:
            log.error(f'Failed to create test run')
            return

        if response.status_code == 200:
            log.info(f'Test run created {response.json()["uid"]}')
            return response.json()
        else:
            log.error('Failed to create test run')

    def update_test_run(self, id: str, access_event: str, title: str, group_title,
                        env: str, label: str, shared_run: bool, shared_run_timeout: str, parallel, ci_build_url: str) -> dict | None:
        request = {
            "access_event": access_event,
            "api_key": self.api_key,
            "title": title,
            "group_title": group_title,
            "env": env,
            "label": label,
            "parallel": parallel,
            "ci_build_url": ci_build_url,
            "shared_run": shared_run,
            "shared_run_timeout": shared_run_timeout
        }
        filtered_request = {k: v for k, v in request.items() if v is not None}
        url = f'{self.base_url}/api/reporter/{id}'
        log.info(f'Updating test run. Run Id: {id}')
        try:
            response = self._send_request_with_retry('put', url, json=filtered_request)
        except Exception as e:
            log.error(f'Failed to update test run')
            return

        if response.status_code == 200:
            log.info(f'Test run updated {response.json()["uid"]}')
            return response.json()
        else:
            log.error('Failed to update test_run')

    def update_test_status(self, run_id: str,
                           rid: str,
                           status: str,
                           title: str,
                           suite_title: str,
                           suite_id: str,
                           test_id: str,
                           message: str,
                           stack: str,
                           run_time: float,
                           artifacts: list[str],
                           steps: str,
                           code: str,
                           example: dict,
                           overwrite: bool | None,
                           meta: dict) -> None:

        log.info(f'Reporting test. Id: {test_id}. Title: {title}')
        request = {
            "status": status,  # Enum: "passed" "failed" "skipped"
            "title": title,
            "suite_title": suite_title,
            "suite_id": suite_id,
            "test_id": test_id,
            "message": message,
            "stack": stack,
            "run_time": run_time,
            "example": example,
            "artifacts": artifacts,
            "steps": steps,
            "code": code,
            "overwrite": overwrite,
            "rid": rid,
            "meta": meta
        }
        filtered_request = {k: v for k, v in request.items() if v is not None}
        url = f'{self.base_url}/api/reporter/{run_id}/testrun?api_key={self.api_key}'
        try:
            response = self._send_request_with_retry('post', url, json=filtered_request)
        except Exception as e:
            log.error(f'Failed to report test')
            return
        if response.status_code == 200:
            log.info('Test status updated')
        else:
            log.error('Failed to report test')

    def batch_tests_upload(self, run_id: str,
                           batch_size: int,
                           tests: list) -> None:
        # TODO: add retry logic
        if not tests:
            log.info(f'No tests to report. Report skipped')
            return

        try:
            log.info(f'Starting batch test report into test run. Run id: {run_id}, number of tests: {len(tests)}, '
                     f'batch size: {batch_size}')
            for i in range(0, len(tests), batch_size):
                batch = tests[i:i+batch_size]
                batch_index = i // batch_size + 1
                request = {
                    'tests': batch,
                    'batch_index': batch_index
                }
                response = self.session.post(f'{self.base_url}/api/reporter/{run_id}/testrun?api_key={self.api_key}',
                                             json=request)
                if response.status_code == 200:
                    log.info(f'Tests status updated. Batch index: {batch_index}')
        except ConnectionError as ce:
            log.error(f'Failed to connect to {self.base_url}: {ce}')
            return
        except HTTPError as he:
            log.error(f'HTTP error occurred while connecting to {self.base_url}: {he}')
            return
        except Exception as e:
            log.error(f'An unexpected exception occurred. Please report an issue: {e}')
            return

    # TODO: I guess this class should be just an API client and used within testRun (testRunConfig)
    def finish_test_run(self, run_id: str, is_final=False) -> None:
        log.info(f'Finishing test run. Run id: {run_id}')
        status_event = 'finish_parallel' if is_final else 'finish'
        url = f'{self.base_url}/api/reporter/{run_id}?api_key={self.api_key}'
        try:
            self._send_request_with_retry('put', url, json={"status_event": status_event})
        except Exception as e:
            log.error(f'Failed to finish test run')
            return

    def disconnect(self):
        self.session.close()
