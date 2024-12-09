import requests, time, logging
from requests.exceptions import HTTPError, ConnectionError
from os.path import join, normpath
from os import getenv
from pytestomatio.utils.helper import safe_string_list
from pytestomatio.testing.testItem import TestItem

log = logging.getLogger('pytestomatio')


class Connector:
    def __init__(self, base_url: str = '', api_key: str = None):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = True
        self.jwt: str = ''
        self.api_key = api_key

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
            response = self.session.post(f'{self.base_url}/api/load?api_key={self.api_key}', json=request)
        except ConnectionError:
            log.error(f'Failed to connect to {self.base_url}')
            return
        except HTTPError:
            log.error(f'Failed to connect to {self.base_url}')
            return
        except Exception as e:
            log.error(f'Generic exception happened. Please report an issue. {e}')
            return

        if response.status_code < 400:
            log.info(f'Tests loaded to {self.base_url}')
        else:
            log.error(f'Failed to load tests to {self.base_url}. Status code: {response.status_code}')

    def get_tests(self, test_metadata: list[TestItem]) -> dict:
        # with safe_request('Failed to get test ids from testomat.io'):
        response = self.session.get(f'{self.base_url}/api/test_data?api_key={self.api_key}')
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
        }
        filtered_request = {k: v for k, v in request.items() if v is not None}
        try:
            response = self.session.post(f'{self.base_url}/api/reporter', json=filtered_request)
        except ConnectionError:
            log.error(f'Failed to connect to {self.base_url}')
            return
        except HTTPError:
            log.error(f'Failed to connect to {self.base_url}')
            return
        except Exception as e:
            log.error(f'Generic exception happened. Please report an issue. {e}')
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
            # "env": env, TODO: enabled when bug with 500 response fixed
            # "label": label, TODO: enabled when bug with 500 response fixed
            "parallel": parallel,
            "ci_build_url": ci_build_url,
        }
        filtered_request = {k: v for k, v in request.items() if v is not None}

        try:
            response = self.session.put(f'{self.base_url}/api/reporter/{id}', json=filtered_request)
        except ConnectionError:
            log.error(f'Failed to connect to {self.base_url}')
            return
        except HTTPError:
            log.error(f'Failed to connect to {self.base_url}')
            return
        except Exception as e:
            log.error(f'Generic exception happened. Please report an issue. {e}')
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
            response = self.session.post(f'{self.base_url}/api/reporter/{run_id}/testrun?api_key={self.api_key}',
                                         json=filtered_request)
        except ConnectionError:
            log.error(f'Failed to connect to {self.base_url}')
            return
        except HTTPError:
            log.error(f'Failed to connect to {self.base_url}')
            return
        except Exception as e:
            log.error(f'Generic exception happened. Please report an issue. {e}')
            return
        if response.status_code == 200:
            log.info('Test status updated')

    # TODO: I guess this class should be just an API client and used within testRun (testRunConfig)
    def finish_test_run(self, run_id: str, is_final=False) -> None:
        status_event = 'finish_parallel' if is_final else 'finish'
        try:
            self.session.put(f'{self.base_url}/api/reporter/{run_id}?api_key={self.api_key}',
                             json={"status_event": status_event})
        except ConnectionError:
            log.error(f'Failed to connect to {self.base_url}')
            return
        except HTTPError:
            log.error(f'Failed to connect to {self.base_url}')
            return
        except Exception as e:
            log.error(f'Generic exception happened. Please report an issue. {e}')
            return

    def disconnect(self):
        self.session.close()
