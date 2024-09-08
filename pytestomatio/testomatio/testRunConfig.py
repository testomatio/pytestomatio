import os
import datetime as dt
import tempfile
from pytestomatio.utils.helper import safe_string_list
from typing import Optional

TESTOMATIO_TEST_RUN_LOCK_FILE = ".testomatio_test_run_id_lock"

class TestRunConfig:
    def __init__(self):
        run_id = os.environ.get('TESTOMATIO_RUN_ID') or os.environ.get('TESTOMATIO_RUN')
        title = os.environ.get('TESTOMATIO_TITLE') if os.environ.get('TESTOMATIO_TITLE') else 'test run at ' + dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shared_run = os.environ.get('TESTOMATIO_SHARED_RUN') in ['True', 'true', '1']
        self.test_run_id = run_id
        self.title = title
        self.environment = safe_string_list(os.environ.get('TESTOMATIO_ENV'))
        self.label = safe_string_list(os.environ.get('TESTOMATIO_LABEL'))
        self.group_title = os.environ.get('TESTOMATIO_RUNGROUP_TITLE')
        # This allows to report tests to the test run by it's id. https://docs.testomat.io/getting-started/running-automated-tests/#reporting-parallel-tests
        self.parallel = False if shared_run else True
        # This allows using test run title to group tests under a single test run. This is needed when running tests in different processes or servers.
        self.shared_run = shared_run
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
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, TESTOMATIO_TEST_RUN_LOCK_FILE)
        with open(temp_file_path, 'w') as f:
            f.write(run_id)


    def get_run_id(self) -> Optional[str]:
        if self.test_run_id:
            return self.test_run_id
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, TESTOMATIO_TEST_RUN_LOCK_FILE)
        if os.path.exists(temp_file_path):
            with open(temp_file_path, 'r') as f:
                self.test_run_id = f.read()
                return self.test_run_id
        return None

    def clear_run_id(self) -> None:
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, TESTOMATIO_TEST_RUN_LOCK_FILE)
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

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