import requests
import logging

from analyzer.testItem import TestItem
from analyzer.testomatio.testomat_item import parse_test_list

log = logging.getLogger('analyzer')


class Connector:
    def __init__(self, username: str, password: str, base_url: str = 'https://app.testomat.io', api_key: str = None):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = True
        self.jwt: str = ''
        self.api_key = api_key
        self.username = username
        self.password = password

    def connect(self, email: str = None, password: str = None):
        request = {'email': email if email else self.username,
                   'password': password if password else self.password}

        # with safe_request('Failed to connect to testomat.io'):
        response = self.session.post(f'{self.base_url}/api/login', json=request)

        if response.status_code == 200:
            log.info(f'Connected to {self.base_url}')
            self.jwt = response.json()['jwt']
            self.session.headers.update({'Authorization': self.jwt})
        else:
            log.error(f'Failed to connect to {self.base_url}. Status code: {response.status_code}')

    def load_tests(self, tests: list[TestItem], no_empty: bool = True, no_detach: bool = True):
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

        # with safe_request('Failed to load tests to testomat.io'):
        response = self.session.post(f'{self.base_url}/api/load?api_key={self.api_key}', json=request)

        if response.status_code == 200:
            log.info(f'Tests loaded to {self.base_url}')
        else:
            log.error(f'Failed to load tests to {self.base_url}. Status code: {response.status_code}')

    def enrich_test_with_ids(self, test_metadata: list[TestItem]) -> None:
        # with safe_request('Failed to get test ids from testomat.io'):
        response = self.session.get(f'{self.base_url}/api/test_data?api_key={self.api_key}')
        response_data = response.json()

        # set test ids from testomatio to test metadata
        if response.status_code == 200:
            tcm_test_data = parse_test_list(response_data)
            for test in test_metadata:
                for tcm_test in tcm_test_data:
                    if test.title == tcm_test.title and test.file_name == tcm_test.file_name:
                        test.id = tcm_test.id
                        tcm_test_data.remove(tcm_test)
                        log.debug(f'test {test.id} matched. There are {len(tcm_test_data)} tests left')
                        break

    def create_test_run(self, title: str, env: str, group_title, parallel) -> str:
        request = {
            "title": title,
            "env": env,
            "group_title": group_title,
            "parallel": parallel
        }
        filtered_request = {k: v for k, v in request.items() if v is not None}
        # with safe_request('Failed to create test run'):
        response = self.session.post(f'{self.base_url}/api/reporter?api_key={self.api_key}', json=filtered_request)
        if response.status_code == 200:
            log.info(f'Test run created {response.json()["uid"]}')
            return response.json()['uid']

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
        # with safe_request(f'Failed to update test status for test id {test_id}'):
        response = self.session.post(f'{self.base_url}/api/reporter/{run_id}/testrun?api_key={self.api_key}',
                                     json=filtered_request)
        if response.status_code == 200:
            log.info('Test status updated')

    def finish_test_run(self, run_id: str) -> None:
        self.session.put(f'{self.base_url}/api/reporter/{run_id}?api_key={self.api_key}',
                         json={"status_event": "finish"})

    def disconnect(self):
        self.session.close()
