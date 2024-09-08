import os, pytest, logging, json
import time
from pytest import Parser, Session, Config, Item, CallInfo, hookimpl
from pytestomatio.connect.connector import Connector
from pytestomatio.decor.decorator_updater import update_tests
from pytestomatio.testomatio.testRunConfig import TestRunConfig
from pytestomatio.testing.testItem import TestItem
from pytestomatio.connect.s3_connector import S3Connector
from .testomatio.testomatio import Testomatio
from pytestomatio.utils.helper import add_and_enrich_tests, get_test_mapping, collect_tests
from pytestomatio.utils.parser_setup import parser_options
from pytestomatio.utils import helper
from pytestomatio.utils import validations

log = logging.getLogger(__name__)
log.setLevel('INFO')

metadata_file = 'metadata.json'
decorator_name = 'testomatio'
testomatio = 'testomatio'


def pytest_addoption(parser: Parser) -> None:
    parser_options(parser, testomatio)


def pytest_configure(config: Config):
    config.addinivalue_line(
        "markers", "testomatio(arg): built in marker to connect test case with testomat.io by unique id"
    )

    option = validations.validate_option(config)
    if option == 'debug':
        return

    pytest.testomatio = Testomatio(TestRunConfig())

    url = config.getini('testomatio_url')
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





def pytest_collection_modifyitems(session: Session, config: Config, items: list[Item]) -> None:
    if config.getoption(testomatio) is None:
        return
    
    # Filter by --test-id if provided
    test_ids_option = config.getoption("test_id")
    if test_ids_option:
        test_ids = test_ids_option.split("|")
        # Remove "@" from the start of test IDs if present
        test_ids = [test_id.lstrip("@T") for test_id in test_ids]
        selected_items = []
        deselected_items = []

        for item in items:
            # Check if the test has the marker with the ID we are looking for
            for marker in item.iter_markers(name="testomatio"):
                marker_id = marker.args[0].lstrip("@T")  # Strip "@" from the marker argument
                if marker_id in test_ids:
                    selected_items.append(item)
                    break
            else:
                deselected_items.append(item)

        items[:] = selected_items
        config.hook.pytest_deselected(items=deselected_items)

    meta, test_files, test_names = collect_tests(items)
    match config.getoption(testomatio):
        case 'sync':
            pytest.testomatio.connector.load_tests(
                meta,
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

            s3_details = helper.read_env_s3_keys(run_details)

            if all(s3_details):
                pytest.testomatio.s3_connector = S3Connector(*s3_details)
                pytest.testomatio.s3_connector.login()
            else:
                # TODO: handle missing credentials
                pytest.testomatio.s3_connector = S3Connector()
                
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
        'suite_title': test_item.file_name,
        'suite_id': None,
        'test_id': test_id,
        'message': None,
        'stack': None,
        'example': None,
        'artifacts': test_item.artifacts,
        'steps': None,
        'code': None,
    }

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
            request['example'] = item.callspec.params

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
