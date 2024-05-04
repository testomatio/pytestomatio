import datetime as dt
import uuid
from re import sub
from pytestomatio.utils.worker_sync import SyncLock


class TestRunConfig:
    def __init__(
            self,
            id: str = None,
            title: str = None,
            group_title: str = None,
            environment: str = None,
            label: str = None,
            parallel: bool = True,
            shared_run: bool = True
    ):
        self.test_run_id = id
        self.title = title if title else 'test run at ' + dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.environment = self.safe_string_list(environment)
        self.label = self.safe_string_list(label)
        self.group_title = group_title
        self.parallel = parallel
        self.shared_run = shared_run
        self.status_request = {}
        self.lock = SyncLock()

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
        self.environment = self.safe_string_list(env)

    def safe_string_list(self, param: str):
        if not param:
            return None
        return ",".join([sub(r"\s", "", part) for part in param.split(',')])
