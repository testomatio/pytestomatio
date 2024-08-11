import os
import datetime as dt
from pytestomatio.utils.helper import safe_string_list


class TestRunConfig:
    def __init__(self, parallel: bool = True):
        self.test_run_id = None
        run = os.environ.get('TESTOMATIO_RUN')
        title = os.environ.get('TESTOMATIO_TITLE')
        run_or_title = run if run else title
        self.title = run_or_title if run_or_title else 'test run at ' + dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.environment = safe_string_list(os.environ.get('TESTOMATIO_ENV'))
        self.label = safe_string_list(os.environ.get('TESTOMATIO_LABEL'))
        self.group_title = os.environ.get('TESTOMATIO_RUNGROUP_TITLE')
        self.parallel = parallel
        # stands for run with shards
        self.shared_run = run_or_title is not None
        self.status_request = {}

    def to_dict(self) -> dict:
        result = dict()
        if self.test_run_id:
            result['id'] = self.test_run_id
        result['title'] = self.title
        result['group_title'] = self.group_title
        result['env'] = self.environment
        result['label'] = self.label
        result['parallel'] = self.parallel
        result['shared_run'] = self.shared_run
        return result

    def set_env(self, env: str) -> None:
        self.environment = safe_string_list(env)

    def save_run_id(self, run_id: str) -> None:
        self.test_run_id = run_id
        with open('.temp_test_run_id', 'w') as f:
            f.write(run_id)

    def get_run_id(self) -> str or None:
        if self.test_run_id:
            return self.test_run_id
        if os.path.exists('.temp_test_run_id'):
            with open('.temp_test_run_id', 'r') as f:
                self.test_run_id = f.read()
                return self.test_run_id
        return None

    def clear_run_id(self) -> None:
        if os.path.exists('.temp_test_run_id'):
            os.remove('.temp_test_run_id')
