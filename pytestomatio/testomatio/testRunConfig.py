import os
import datetime as dt
from pytestomatio.utils.helper import safe_string_list
from typing import Optional


class TestRunConfig:
    def __init__(self, parallel: bool = True):
        self.test_run_id = os.environ.get('TESTOMATIO_RUN_ID') or None
        run = os.environ.get('TESTOMATIO_RUN') or None
        title = os.environ.get('TESTOMATIO_TITLE') or None
        run_or_title = run if run else title
        self.title = run_or_title if run_or_title else 'test run at ' + dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.environment = safe_string_list(os.environ.get('TESTOMATIO_ENV'))
        self.label = safe_string_list(os.environ.get('TESTOMATIO_LABEL'))
        self.group_title = os.environ.get('TESTOMATIO_RUNGROUP_TITLE') or None
        self.parallel = parallel
        # stands for run with shards
        self.shared_run = run_or_title is not None
        self.status_request = {}
        self.build_url = self.resolve_build_url()

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
        result['ci_build_url'] = self.build_url
        return result

    def set_env(self, env: str) -> None:
        self.environment = safe_string_list(env)

    def save_run_id(self, run_id: str) -> None:
        self.test_run_id = run_id
        with open('.temp_test_run_id', 'w') as f:
            f.write(run_id)

    def get_run_id(self) -> Optional[str]:
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

    def resolve_build_url(self) -> Optional[str]:
        # You might not always want the build URL to change in the Testomat.io test run
        if os.getenv('TESTOMATIO_CI_DOWNSTREAM'): 
            return None
        build_url = os.getenv('BUILD_URL') or os.getenv('CI_JOB_URL') or os.getenv('CIRCLE_BUILD_URL')

        # GitHub Actions URL
        if not build_url and os.getenv('GITHUB_RUN_ID'):
            github_server_url = os.getenv('GITHUB_SERVER_URL')
            github_repository = os.getenv('GITHUB_REPOSITORY')
            github_run_id = os.getenv('GITHUB_RUN_ID')
            build_url = f"{github_server_url}/{github_repository}/actions/runs/{github_run_id}"

        # Azure DevOps URL
        if not build_url and os.getenv('SYSTEM_TEAMFOUNDATIONCOLLECTIONURI'):
            collection_uri = os.getenv('SYSTEM_TEAMFOUNDATIONCOLLECTIONURI')
            project = os.getenv('SYSTEM_TEAMPROJECT')
            build_id = os.getenv('BUILD_BUILDID')
            build_url = f"{collection_uri}/{project}/_build/results?buildId={build_id}"

        if build_url and not build_url.startswith('http'):
            build_url = None

        return build_url