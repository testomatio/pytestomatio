import requests
from requests.exceptions import HTTPError, ConnectionError
import logging
from os.path import join, normpath
from os import getenv
from pytestomatio.utils.helper import safe_string_list
from pytestomatio.testing.testItem import TestItem

log = logging.getLogger('pytestomatio')


class Connector:
    def __init__(self, base_url: str = 'https://app.testomat.io', api_key: str = None):
        self.base_url = base_url
        self._session = requests.Session()
        self.jwt: str = ''
        self.api_key = api_key

    @property
    def session(self):
        """Get the session, creating it and applying proxy settings if necessary."""
        if self._session is None:
            self._session = requests.Session()
            self._apply_proxy_settings()
        return self._session

    @session.setter
    def session(self, value):
        """Allow setting a custom session, while still applying proxy settings."""
        self._session = value
        self._apply_proxy_settings()

    def _apply_proxy_settings(self):
        """Apply proxy settings based on environment variables."""
        http_proxy = getenv("HTTP_PROXY")
        if http_proxy:
            self._session.proxies = {"http": http_proxy, "https": http_proxy}
            self._session.verify = False
        else:
            self._session.proxies.clear()  # Clear proxies if HTTP_PROXY is not set
            self._session.verify = True

    def load_tests(
            self,
            tests: list[TestItem],
            no_empty: bool = False,
            no_detach: bool = False,
            structure: bool = False,
            create: bool = False,
            directory: str = None
    ):
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
                "file": test.file_path if structure else (
                    test.file_name if directory is None else normpath(join(directory, test.file_name))),
                "labels": safe_string_list(getenv('TESTOMATIO_SYNC_LABELS')),
            })

        try:
            response = self._session.post(f'{self.base_url}/api/load?api_key={self.api_key}', json=request)
        except ConnectionError as ce:
            log.error(f'Failed to connect to {self.base_url}: {ce}')
            return
        except HTTPError as he:
            log.error(f'HTTP error occurred while connecting to {self.base_url}: {he}')
            return
        except Exception as e:
            log.error(f'An unexpected exception occurred. Please report an issue: {e}')
            return

        if response.status_code < 400:
            log.info(f'Tests loaded to {self.base_url}')
        else:
            log.error(f'Failed to load tests to {self.base_url}. Status code: {response.status_code}')

    def get_tests(self, test_metadata: list[TestItem]) -> dict:
        # with safe_request('Failed to get test ids from testomat.io'):
        response = self._session.get(f'{self.base_url}/api/test_data?api_key={self.api_key}')
        return response.json()

    def create_test_run(self, title: str, group_title, env: str, label: str, shared_run: bool, parallel, ci_build_url: str) -> dict | None:
        request = {
            "api_key": self.api_key,
            "title": title,
            "group_title": group_title,
            "env": env,
            "label": label,
            "parallel": parallel,
            "ci_build_url": ci_build_url,
            "shared_run": shared_run
        }
        filtered_request = {k: v for k, v in request.items() if v is not None}
        try:
            response = self._session.post(f'{self.base_url}/api/reporter', json=filtered_request)
        except ConnectionError as ce:
            log.error(f'Failed to connect to {self.base_url}: {ce}')
            return
        except HTTPError as he:
            log.error(f'HTTP error occurred while connecting to {self.base_url}: {he}')
            return
        except Exception as e:
            log.error(f'An unexpected exception occurred. Please report an issue: {e}')
            return

        if response.status_code == 200:
            log.info(f'Test run created {response.json()["uid"]}')
            return response.json()

    def update_test_run(self, id: str, title: str, group_title,
                        env: str, label: str, shared_run: bool, parallel, ci_build_url: str) -> dict | None:
        request = {
            "api_key": self.api_key,
            "title": title,
            "group_title": group_title,
            "env": env,
            "label": label,
            "parallel": parallel,
            "ci_build_url": ci_build_url,
            "shared_run": shared_run
        }
        filtered_request = {k: v for k, v in request.items() if v is not None}

        try:
            response = self._session.put(f'{self.base_url}/api/reporter/{id}', json=filtered_request)
        except ConnectionError as ce:
            log.error(f'Failed to connect to {self.base_url}: {ce}')
            return
        except HTTPError as he:
            log.error(f'HTTP error occurred while connecting to {self.base_url}: {he}')
            return
        except Exception as e:
            log.error(f'An unexpected exception occurred. Please report an issue: {e}')
            return

        if response.status_code == 200:
            log.info(f'Test run updated {response.json()["uid"]}')
            return response.json()

    def update_test_status(self, run_id: str,
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
                           example: dict) -> None:

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
            "code": code
        }
        filtered_request = {k: v for k, v in request.items() if v is not None}
        try:
            response = self._session.post(f'{self.base_url}/api/reporter/{run_id}/testrun?api_key={self.api_key}',
                                         json=filtered_request)
        except ConnectionError as ce:
            log.error(f'Failed to connect to {self.base_url}: {ce}')
            return
        except HTTPError as he:
            log.error(f'HTTP error occurred while connecting to {self.base_url}: {he}')
            return
        except Exception as e:
            log.error(f'An unexpected exception occurred. Please report an issue: {e}')
            return
        if response.status_code == 200:
            log.info('Test status updated')

    # TODO: I guess this class should be just an API client and used within testRun (testRunConfig)
    def finish_test_run(self, run_id: str, is_final=False) -> None:
        status_event = 'finish_parallel' if is_final else 'finish'
        try:
            self._session.put(f'{self.base_url}/api/reporter/{run_id}?api_key={self.api_key}',
                             json={"status_event": status_event})
        except ConnectionError as ce:
            log.error(f'Failed to connect to {self.base_url}: {ce}')
            return
        except HTTPError as he:
            log.error(f'HTTP error occurred while connecting to {self.base_url}: {he}')
            return
        except Exception as e:
            log.error(f'An unexpected exception occurred. Please report an issue: {e}')
            return

    def disconnect(self):
        self._session.close()
