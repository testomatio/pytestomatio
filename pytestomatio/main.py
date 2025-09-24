import os, pytest, logging, json, time
import warnings

from pytest import Parser, Session, Config, Item, CallInfo
from pytestomatio.connect.connector import Connector
from pytestomatio.connect.s3_connector import S3Connector
from pytestomatio.testing.testItem import TestItem
from pytestomatio.decor.decorator_updater import update_tests

from pytestomatio.utils.helper import add_and_enrich_tests, get_test_mapping, collect_tests, read_env_s3_keys
from pytestomatio.utils.parser_setup import parser_options
from pytestomatio.utils import validations

from pytestomatio.testomatio.testRunConfig import TestRunConfig
from pytestomatio.testomatio.testomatio import Testomatio
from pytestomatio.testomatio.filter_plugin import TestomatioFilterPlugin

log = logging.getLogger(__name__)
log.setLevel('INFO')

metadata_file = 'metadata.json'
decorator_name = 'testomatio'
testomatio = 'testomatio'
TESTOMATIO_URL = 'https://app.testomat.io'


def pytest_addoption(parser: Parser) -> None:
    parser_options(parser, testomatio)


def pytest_collection(session):
    """Capture original collected items before any filters are applied."""
    # This hook is called after initial test collection, before other filters.
    # We'll store the items in a session attribute for later use.
    session._pytestomatio_original_collected_items = []


def pytest_configure(config: Config):
    config.addinivalue_line(
        "markers", "testomatio(arg): built in marker to connect test case with testomat.io by unique id"
    )

    option = validations.validate_option(config)
    if option == 'debug':
        return

    pytest.testomatio = Testomatio(TestRunConfig())

    url = os.environ.get('TESTOMATIO_URL') or config.getini('testomatio_url') or TESTOMATIO_URL
    project = os.environ.get('TESTOMATIO')

    pytest.testomatio.connector = Connector(url, project)
    run_env = config.getoption('testRunEnv')
    if run_env:
        pytest.testomatio.test_run_config.set_env(run_env)

    if config.getoption(testomatio) and config.getoption(testomatio).lower() == 'report':
        run: TestRunConfig = pytest.testomatio.test_run_config

        # for xdist - main process
        if not hasattr(config, 'workerinput'):
            run_id = pytest.testomatio.test_run_config.test_run_id
            if not run_id:
                run_details = pytest.testomatio.connector.create_test_run(**run.to_dict())
                if run_details:
                    run_id = run_details.get('uid')
                    run.save_run_id(run_id)
                else:
                    log.error("Failed to create testrun on Testomat.io")

    # Mark our pytest_collection_modifyitems hook to run last,
    # so that it sees the effect of all built-in and other filters first.
    # This ensures we only apply our OR logic after other filters have done their job.
    config.pluginmanager.register(TestomatioFilterPlugin(), "testomatio_filter_plugin")

@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session: Session, config: Config, items: list[Item]) -> None:
    if config.getoption(testomatio) is None:
        return

    # Store a copy of all initially collected items (the first time this hook runs)
    # The first call to this hook happens before built-in filters like -k, -m fully apply.
    # By the time this runs, items might still be unfiltered or only partially filtered.
    # To ensure we get the full original list, we use pytest_collection hook above.
    if not session._pytestomatio_original_collected_items:
        # The initial call here gives us the full collected list of tests
        session._pytestomatio_original_collected_items = items[:]

    # At this point, if other plugins or internal filters like -m and -k run,
    # they may modify `items` (removing some tests). We run after them by using a hook wrapper
    # or a trylast marker to ensure our logic runs after most filters.

    meta, test_files, test_names = collect_tests(items)
    match config.getoption(testomatio):
        case 'sync':
            tests = [item for item in meta if item.type != 'bdd']
            if not len(tests) == len(meta):
                warnings.warn('BDD tests excluded from sync. You need to sync them separately into another project '
                              'via check-cucumber. For details, see https://github.com/testomatio/check-cucumber')
            pytest.testomatio.connector.load_tests(
                tests,
                no_empty=config.getoption('no_empty'),
                no_detach=config.getoption('no_detach'),
                structure=config.getoption('keep_structure'),
                create=config.getoption('create'),
                directory=config.getoption('directory')
            )
            testomatio_tests = pytest.testomatio.connector.get_tests(meta)
            add_and_enrich_tests(meta, test_files, test_names, testomatio_tests, decorator_name)
            pytest.exit('Sync completed without test execution')
        case 'remove':
            mapping = get_test_mapping(meta)
            for test_file in test_files:
                update_tests(test_file, mapping, test_names, decorator_name, remove=True)
            pytest.exit('Sync completed without test execution')
        case 'report':
            # for xdist workers - get run id from the main process
            run: TestRunConfig = pytest.testomatio.test_run_config
            run.get_run_id()

            # send update without status just to get artifact details from the server
            run_details = pytest.testomatio.connector.update_test_run(**run.to_dict())

            if run_details is None:
                log.error('Test run failed to create. Reporting skipped')
                return

            s3_details = read_env_s3_keys(run_details)

            if all(s3_details):
                pytest.testomatio.s3_connector = S3Connector(*s3_details)
                pytest.testomatio.s3_connector.login()
                
        case 'debug':
            with open(metadata_file, 'w') as file:
                data = json.dumps([i.to_dict() for i in meta], indent=4)
                file.write(data)
                pytest.exit('Debug file created. Exiting...')
        case _:
            raise Exception('Unknown pytestomatio parameter. Use one of: add, remove, sync, debug')

def pytest_runtest_makereport(item: Item, call: CallInfo):
    pytest.testomatio_config_option = item.config.getoption(testomatio)
    if pytest.testomatio_config_option is None or pytest.testomatio_config_option != 'report':
        return
    elif not pytest.testomatio.test_run_config.test_run_id:
        return

    test_item = TestItem(item)
    if test_item.id is None:
        test_id = None
    else:
        test_id = test_item.id if not test_item.id.startswith("@T") else test_item.id[2:]

    request = {
        'status': None,
        'title': test_item.exec_title,
        'run_time': call.duration,
        'suite_title': test_item.suite_title,
        'suite_id': None,
        'test_id': test_id,
        'message': None,
        'stack': None,
        'example': None,
        'artifacts': test_item.artifacts,
        'steps': None,
        'code': None,
        'overwrite': None,
    }

    if pytest.testomatio.test_run_config.update_code and test_item.type != 'bdd':
        request['code'] = test_item.source_code
        request['overwrite'] = True

    # TODO: refactor it and use TestItem setter to upate those attributes
    if call.when in ['setup', 'call']:
        if call.excinfo is not None:
            if call.excinfo.typename == 'Skipped':
                request['status'] = 'skipped'
                request['message'] = str(call.excinfo.value)
            else:
                request['message'] = str(call.excinfo.value)
                request['stack'] = '\n'.join((str(tb) for tb in call.excinfo.traceback))
                request['status'] = 'failed'
        else:
            request['status'] = 'passed' if call.when == 'call' else request['status']

        if hasattr(item, 'callspec'):
            request['example'] = test_item.safe_params(item.callspec.params)

    if item.nodeid not in pytest.testomatio.test_run_config.status_request:
        pytest.testomatio.test_run_config.status_request[item.nodeid] = request
    else:
        for key, value in request.items():
            if key == 'title' and call.when == 'teardown':
                continue
            if value is not None:
                pytest.testomatio.test_run_config.status_request[item.nodeid][key] = value


def pytest_runtest_logfinish(nodeid, location):
    if not hasattr(pytest, 'testomatio_config_option'):
        return
    if pytest.testomatio_config_option is None or pytest.testomatio_config_option != 'report':
        return
    elif not pytest.testomatio.test_run_config.test_run_id:
        return

    for nodeid, request in pytest.testomatio.test_run_config.status_request.items():
        if request['status']:
            pytest.testomatio.connector.update_test_status(run_id=pytest.testomatio.test_run_config.test_run_id,
                                                           **request)
    pytest.testomatio.test_run_config.status_request = {}


def pytest_unconfigure(config: Config):
    if not hasattr(pytest, 'testomatio'):
        return

    run: TestRunConfig = pytest.testomatio.test_run_config
    # for xdist - main process
    if not hasattr(config, 'workerinput'):
        time.sleep(1)
        pytest.testomatio.connector.finish_test_run(run.test_run_id, True)
        run.clear_run_id()

    # for xdist - worker process
    else:
        pytest.testomatio.connector.finish_test_run(run.test_run_id, False)
