import datetime as dt


class TestRunConfig:
    def __init__(self, title: str = None,
                 environment: str = None,
                 group_title: str = None,
                 parallel: bool = False):
        self.test_run_id = None
        self.title = title if title else 'test run at ' + dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.environment = environment
        self.group_title = group_title
        self.parallel = parallel
        self.status_request = []

    def to_dict(self) -> dict:
        result = dict()
        result['title'] = self.title
        result['env'] = self.environment
        result['group_title'] = self.group_title
        result['parallel'] = self.parallel
        return result
