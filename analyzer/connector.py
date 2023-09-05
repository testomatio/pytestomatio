import requests
import logging

from .testItem import TestItem

log = logging.getLogger('analyzer')


class Connector:
    def __init__(self, base_url: str = 'https://app.testomat.io', api_key: str = None):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = True
        self.jwt: str = ''
        self.api_key = api_key

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
                "name": test.user_title,
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

    def get_tests(self, test_metadata: list[TestItem]) -> dict:
        # with safe_request('Failed to get test ids from testomat.io'):
        response = self.session.get(f'{self.base_url}/api/test_data?api_key={self.api_key}')
        return response.json()

    def create_test_run(self, title: str, env: str, group_title, parallel) -> dict:
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
