import requests
import logging
from requests import Response

import analyzer.testomatio
from analyzer.testItem import TestItem
from analyzer.testomatio.testomat_item import parse_test_list

log = logging.getLogger(__name__)


class Connector:
    def __init__(self, base_url: str = 'https://app.testomat.io', api_key: str = None):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = False
        self.jwt: str = ''
        self.api_key = api_key

    def connect(self, email: str, password: str):
        try:
            response = self.session.post(f'{self.base_url}/api/login', json={'email': email, 'password': password})
        except Exception as e:
            log.error(f'Failed to connect to {self.base_url}. Exception: {e}')
            return
        if response.status_code == 200:
            log.info(f'Connected to {self.base_url}')
            self.jwt = response.json()['jwt']
            self.session.headers.update({'Authorization': self.jwt})
        else:
            log.error(f'Failed to connect to {self.base_url}. Status code: {response.status_code}')

    def load_tests(self, tests: list[TestItem], no_empty: bool = True, no_detach: bool = False):
        request = {
            "framework": "pytest",
            "language": "python",
            "noempty": no_empty,
            "no-detach": no_detach,
            "structure": True,
            "sync": True,
            "tests": []
        }
        for test in tests:
            request['tests'].append({
                "name": test.title,
                "suites": [
                    test.file_name,
                    test.class_name
                ],
                "code": test.source_code,
                "file": test.file_name
            })
        try:
            response = self.session.post(f'{self.base_url}/api/load?api_key={self.api_key}', json=request)
            log.info(f'test upload to testomat.io response: {response.status_code}')
        except Exception as e:
            log.error(f'Failed to load tests to {self.base_url}. Exception: {e}')
            return
        if response.status_code == 200:
            log.info(f'Tests loaded to {self.base_url}')
        else:
            log.error(f'Failed to load tests to {self.base_url}. Status code: {response.status_code}')

    def enrich_test_with_ids(self, test_metadata: list[TestItem]) -> None:
        try:
            response = self.session.get(f'{self.base_url}/api/test_data?api_key={self.api_key}')
            response_data = response.json()
        except Exception as e:
            log.error(f'Failed to get test ids from {self.base_url}. Exception: {e}')
            return

        # set test ids from testomatio to test metadata
        tcm_test_data = parse_test_list(response_data)
        log.debug(f'there are {len(tcm_test_data)} tests in testomat.io')
        log.debug(f'there are {len(test_metadata)} tests in test metadata')
        for test in test_metadata:
            for tcm_test in tcm_test_data:
                if test.title == tcm_test.title and test.file_name == tcm_test.file_name:
                    test.id = tcm_test.id
                    tcm_test_data.remove(tcm_test)
                    log.debug(f'test {test.id} matched. There are {len(tcm_test_data)} tests left')
                    break

    def create_test_run(self, title: str, tags: list[str], env: str, group_title, parallel) -> str:
        request = {
            "title": title,
            "tags": tags,
            "env": env,
            "group_title": group_title,
            "parallel": parallel
        }
        try:
            response = self.session.post(f'{self.base_url}/api/reporter/?api_key={self.api_key}',
                                         json=request)
            log.debug(f'test run created: {response.status_code}')
            return response.json()['uid']
        except Exception as e:
            log.error(f'Test run creation failed. Exception: {e}')
            return ''

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
                           code: str) -> None:

        request = {
            "status": status,  # Enum: "passed" "failed" "skipped"
            "title": title,
            "suite_title": suite_title,
            "suite_id": suite_id,
            "test_id": test_id,
            "message": message,
            "stack": stack,
            "run_time": run_time,
            "example": {},
            "artifacts": artifacts,
            "steps": steps,
            "code": code
        }
        try:
            response = self.session.post(f'{self.base_url}/api/reporter/{run_id}/testrun?api_key={self.api_key}',
                                         json=request)
            log.debug(f'test status update response: {response.status_code}')
        except Exception as e:
            log.error(f'test id {test_id} status update failed. Exception: {e}')
            return

    def disconnect(self):
        self.session.close()
