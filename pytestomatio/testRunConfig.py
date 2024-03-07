import datetime as dt


class TestRunConfig:
    def __init__(
            self,
            title: str = None,
            group_title: str = None,
            environment: str = None,
            label: str = None,
            parallel: bool = False,
            shared_run: bool = False
        ):
        self.test_run_id = None
        self.title = title if title else 'test run at ' + dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.environment = environment
        self.label = label
        self.group_title = group_title
        self.parallel = parallel
        if shared_run and not title:
            raise ValueError('TESTOMATIO_SHARED_RUN can only be used together with TESTOMATIO_TITLE')
        self.shared_run = shared_run
        self.status_request = {}

    def to_dict(self) -> dict:
        result = dict()
        result['title'] = self.title
        result['group_title'] = self.group_title
        result['env'] = self.environment
        result['label'] = self.label
        result['parallel'] = self.parallel
        result['shared_run'] = self.shared_run
        return result
    
    def set_run_id(self, run_id: str) -> None:
        self.test_run_id = run_id

    def set_env(self, env: str) -> None:
        self.environment = [part.strip() for part in env.split(',')]
