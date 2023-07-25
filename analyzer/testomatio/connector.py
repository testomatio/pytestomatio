import requests
import logging
from requests import Response
from analyzer.testItem import TestItem
from analyzer.testomatio.testomat_test import parse_test_list

log = logging.getLogger(__name__)


class Connector:
    def __int__(self, base_url: str = 'https://app.testomat.io'):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = False
        self.jwt: str

    def connect(self, email: str, password: str):
        response: Response
        try:
            response = self.session.post(f'{self.base_url}/api/login', json={'email': email, 'password': password})
        except Exception as e:
            log.error(f'Failed to connect to {self.base_url}. Exception: {e}')
            return
        if response.status_code == 200:
            log.info(f'Connected to {self.base_url}')
            self.jwt = response.json()['jwt']
            self.session.headers.update({'Authorization', self.jwt})
        else:
            log.error(f'Failed to connect to {self.base_url}. Status code: {response.status_code}')

    def load_tests(self, api_key: str, tests: list[TestItem], no_empty: bool = True, no_detach: bool = True):
        response: Response
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
            response = self.session.post(f'{self.base_url}/api/load?api_key={api_key}', json=request)
        except Exception as e:
            log.error(f'Failed to load tests to {self.base_url}. Exception: {e}')
            return
        if response.status_code == 200:
            log.info(f'Tests loaded to {self.base_url}')
        else:
            log.error(f'Failed to load tests to {self.base_url}. Status code: {response.status_code}')

    def enrich_test_with_ids(self, api_key: str, test_metadata: list[TestItem]) -> None:
        try:
            response = self.session.get(f'{self.base_url}/api/test_data?api_key={api_key}')
            response_data = response.json()
        except Exception as e:
            log.error(f'Failed to get test ids from {self.base_url}. Exception: {e}')
            return

        # set test ids from testomatio to test metadata
        tcm_test_data = parse_test_list(response_data)
        for test in test_metadata:
            for tcm_test in tcm_test_data:
                if test.title == tcm_test.title and test.file_name == tcm_test.file_name:
                    test.id = tcm_test.id
                    break

    def update_test_status(self, test_id: int, status: str) -> None:
        pass

    def disconnect(self):
        self.session.close()


# mock test ids function
def mock_tests(tests: list[TestItem]):
    for index, test in enumerate(tests):
        test.id = index + 1
