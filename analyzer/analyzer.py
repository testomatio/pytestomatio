import pytest
import json

from pytest import Parser, Session, Config, Item, CallInfo
from .connector import Connector
from .decorator_updater import update_tests
from .testRunConfig import TestRunConfig
from .testItem import TestItem
from .s3_connector import S3Connector
from .helper import add_and_enrich_tests, get_test_mapping, get_functions_source_by_name, collect_tests
import logging
import os

log = logging.getLogger(__name__)
log.setLevel('INFO')

metadata_file = 'metadata.json'
decorator_name = 'testomatio'
analyzer_option = 'analyzer'

help_text = 'analyze tests, connect test with testomat.io. Use parameters:\n' \
            'add - upload tests and set test ids in the code\n' \
            'remove - removes testomat.io ids from the ALL tests\n' \
            'sync - allows to share sync test run status with testomat.io\n' \
            'debug - saves analyzed test metadata to the json in the test project root\n'


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(f'--{analyzer_option}',
                     action='store',
                     help=help_text)
    parser.addoption(f'--testRunEnv',
                     action='store',
                     help='specify test run environment for testomat.io. Works only with --analyzer sync')
    parser.addoption(f'--create',
                    action='store_true',
                    default=False,
                    dest="create",
                    help='To import tests with Test IDs set in source code into a project use --create option. In this case, a new project will be populated with the same Test IDs.. Use --add together with --create option to enable this behavior.')
    parser.addoption(f'--no-empty',
                     action='store_true',
                     default=False,
                     dest="no_empty",
                     help='Delete empty suites. If tests were marked with IDs and imported to already created suites in Testomat.io newly imported suites may become empty. Use --add together with --no-empty option to clean them up after import.')
    parser.addoption(f'--no-detach',
                     action='store_true',
                     default=False,
                     dest="no_detach",
                     help='Disable detaching tests. If a test from a previous import was not found on next import it is marked as "detached". This is done to ensure that deleted tests are not staying in Testomatio while deleted in codebase. To disable this behavior and don\'t mark anything on detached on import use --add together with --no-detached option.')
    parser.addoption(f'--keep-structure',
                     action='store_true',
                     default=False,
                     dest="keep_structure",
                     help='Keep structure of source code. If suites are not created in Testomat.io they will be created based on the file structure. Use --add together with --structure option to enable this behavior.')
    parser.addini('testomatio_url', 'testomat.io base url', default='https://app.testomat.io')


def pytest_configure(config: Config):
    config.addinivalue_line(
        "markers", "testomatio(arg): built in marker to connect test case with testomat.io by unique id"
    )

    pytest.analyzer_test_run_config = TestRunConfig(group_title=os.environ.get('TESTOMATIO_RUNGROUP_TITLE'))
    pytest.s3_connector = None

    if config.getoption(analyzer_option) in ('add', 'remove', 'sync'):
        url = config.getini('testomatio_url')
        project = os.environ.get('TESTOMATIO')
        if project is None:
            pytest.exit('TESTOMATIO env variable is not set')
        connector = Connector(url, project)
        pytest.connector = connector
        if config.getoption('testRunEnv'):
            pytest.analyzer_test_run_config.environment = config.getoption('testRunEnv')


def pytest_collection_modifyitems(session: Session, config: Config, items: list[Item]) -> None:
    if config.getoption(analyzer_option):
        meta, test_files, test_names = collect_tests(items)
        match config.getoption(analyzer_option):
            case 'add':
                connector: Connector = pytest.connector
                connector.load_tests(
                    meta,
                    no_empty=config.getoption('no_empty'),
                    no_detach=config.getoption('no_detach'),
                    structure=config.getoption('keep_structure'),
                    create=config.getoption('create')
                )
                testomatio_tests = connector.get_tests(meta)
                add_and_enrich_tests(meta, test_files, test_names, testomatio_tests, decorator_name)
                pytest.exit(
                    f'{len(items)} found. {len(meta)} unique test functions data collected and updated.'
                    f'Exit without test execution')
            case 'remove':
                mapping = get_test_mapping(meta)
                for test_file in test_files:
                    update_tests(test_file, mapping, test_names, decorator_name, remove=True)
                pytest.exit(
                    f'{len(items)} found. tests ids removed. Exit without test execution')
            case 'sync':
                connector: Connector = pytest.connector
                test_config = pytest.analyzer_test_run_config
                run_details = connector.create_test_run(**test_config.to_dict())
                if run_details is None:
                    log.error('Test run failed to create. Reporting skipped')
                    return
                pytest.analyzer_test_run_config.test_run_id = run_details['uid']

                if run_details.get('artifacts'):
                    s3_access_key = run_details['artifacts'].get('ACCESS_KEY_ID')
                    s3_secret_key = run_details['artifacts'].get('SECRET_ACCESS_KEY')
                    s3_endpoint = run_details['artifacts'].get('ENDPOINT')
                    s3_bucket = run_details['artifacts'].get('BUCKET')
                    if all((s3_access_key, s3_secret_key, s3_endpoint, s3_bucket)):
                        pytest.s3_connector = S3Connector(s3_access_key, s3_secret_key, s3_endpoint, s3_bucket)
                        pytest.s3_connector.login()
                    else:
                        pytest.s3_connector = S3Connector('', '', '', '')
            case 'debug':
                with open(metadata_file, 'w') as file:
                    data = json.dumps([i.to_dict() for i in meta], indent=4)
                    file.write(data)
                pytest.exit(
                    f'saved metadata to {metadata_file}. Exit without test execution')
            case _:
                pytest.exit('Unknown analyzer parameter. Use one of: add, remove, sync, debug')


def pytest_runtest_makereport(item: Item, call: CallInfo):
    pytest.analyzer_config_option = item.config.getoption(analyzer_option)
    if pytest.analyzer_config_option is None or pytest.analyzer_config_option != 'sync':
        return
    elif not pytest.analyzer_test_run_config.test_run_id:
        return

    test_item = TestItem(item)
    if test_item.id is None:
        test_id = None
    else:
        test_id = test_item.id if not test_item.id.startswith("@T") else test_item.id[2:]

    request = {
        'status': None,
        'title': test_item.title,
        'run_time': call.duration,
        'suite_title': test_item.file_name,
        'suite_id': None,
        'test_id': test_id,
        'message': None,
        'stack': None,
        'example': None,
        'artifacts': None,
        'steps': None,
        'code': None,
    }

    if call.when == 'setup':
        if call.excinfo is not None:
            if call.excinfo.typename == 'Skipped':
                request['status'] = 'skipped'
            else:
                request['message'] = str(call.excinfo.value)
                request['stack'] = '\n'.join((str(tb) for tb in call.excinfo.traceback))
                request['status'] = 'failed'
    if call.when == 'call':
        if call.excinfo is not None:
            request['message'] = str(call.excinfo.value)
            request['stack'] = '\n'.join((str(tb) for tb in call.excinfo.traceback))
            request['status'] = 'failed'
        else:
            request['status'] = 'passed'
        if hasattr(item, 'callspec'):
            example = item.callspec.params
            if type(example) is bytes:
                request['example'] = example.decode('utf-8')
            elif type(example) in (str, int, float, bool):
                request['example'] = item.callspec.params
            else:
                request['example'] = 'object'  # to avoid json serialization error

    if request['status']:
        pytest.analyzer_test_run_config.status_request.append(request)


def pytest_runtest_logfinish(nodeid, location):
    if pytest.analyzer_config_option is None or pytest.analyzer_config_option != 'sync':
        return
    elif not pytest.analyzer_test_run_config.test_run_id:
        return

    for request in pytest.analyzer_test_run_config.status_request:
        if request['status']:
            connector = pytest.connector
            connector.update_test_status(run_id=pytest.analyzer_test_run_config.test_run_id, **request)
    pytest.analyzer_test_run_config.status_request = []


def pytest_sessionfinish(session: Session, exitstatus: int):
    if pytest.analyzer_test_run_config.test_run_id:
        connector = pytest.connector
        connector.finish_test_run(pytest.analyzer_test_run_config.test_run_id)
