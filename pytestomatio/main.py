import os, pytest, logging, json, re

from pytest import Parser, Session, Config, Item, CallInfo
from .connector import Connector
from .decorator_updater import update_tests
from .testRunConfig import TestRunConfig
from .testItem import TestItem
from .s3_connector import S3Connector
from .testomatio import Testomatio
from .helper import add_and_enrich_tests, get_test_mapping, get_functions_source_by_name, collect_tests

log = logging.getLogger(__name__)
log.setLevel('INFO')

metadata_file = 'metadata.json'
decorator_name = 'testomatio'
testomatio = 'testomatio'

help_text = """
            synchronise and connect test with testomat.io. Use parameters:
            sync - synchronize tests and set test ids in the code
            remove - removes testomat.io ids from the ALL test
            report - report tests into testomat.io
            debug - saves analysed test metadata to the json in the test project root
            """


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(f'--{testomatio}',
                     action='store',
                     help=help_text)
    parser.addoption(f'--testRunEnv',
                     action='store',
                     help=f'specify test run environment for testomat.io. Works only with --testomatio sync')
    parser.addoption(f'--create',
                    action='store_true',
                    default=False,
                    dest="create",
                    help="""
                        To import tests with Test IDs set in source code into a project use --create option.
                        In this case a project will be populated with the same Test IDs as in the code.
                        Use --testomatio sync together with --create option to enable this behavior.
                        """
                    )
    parser.addoption(f'--no-empty',
                     action='store_true',
                     default=False,
                     dest="no_empty",
                     help="""
                        Delete empty suites.
                        When tests are marked with IDs and imported to already created suites in Testomat.io newly imported suites may become empty.
                        Use --testomatio sync together with --no-empty option to clean them up after import.
                        """
                     )
    parser.addoption(f'--no-detach',
                     action='store_true',
                     default=False,
                     dest="no_detach",
                     help="""
                        Disable detaching tests.
                        If a test from a previous import was not found on next import it is marked as "detached".
                        This is done to ensure that deleted tests are not staying in Testomatio while deleted in codebase.
                        To disable this behaviour and don\'t mark anything on detached on import use sync together with --no-detached option.
                        """
                     )
    parser.addoption(f'--keep-structure',
                     action='store_true',
                     default=False,
                     dest="keep_structure",
                     help="""
                        Keep structure of source code. If suites are not created in Testomat.io they will be created based on the file structure.
                        Use --testomatio sync together with --structure option to enable this behaviour.
                        """
                    )
    parser.addoption('--directory',
                     default=None,
                     dest="directory",
                     help="""
                        Specify directory to use for test file structure, ex. --directory Windows\\smoke or --directory Linux/e2e
                        Use --testomatio sync together with --directory option to enable this behaviour.
                        Default is the root of the project.
                        Note: --structure option takes precedence over --directory option. If both are used --structure will be used.
                        """
                     )
    parser.addini('testomatio_url', 'testomat.io base url', default='https://app.testomat.io')


def pytest_configure(config: Config):
    config.addinivalue_line(
        "markers", "testomatio(arg): built in marker to connect test case with testomat.io by unique id"
    )
    
    pytest.testomatio = Testomatio()
    test_run_config = TestRunConfig(
        id=os.environ.get('TESTOMATIO_RUN'),
        title=os.environ.get('TESTOMATIO_TITLE'),
        group_title=os.environ.get('TESTOMATIO_RUNGROUP_TITLE'),
        environment=os.environ.get('TESTOMATIO_ENV'),
        shared_run=os.environ.get('TESTOMATIO_SHARED_RUN') in ['True', 'true', '1'],
        label=os.environ.get('TESTOMATIO_LABEL'),
    )
    pytest.testomatio.set_test_run(test_run_config)
    pytest.s3_connector = pytest.testomatio.s3_connector # backward compatibility

    if config.getoption(testomatio) in ('sync', 'report', 'remove'):
        url = config.getini('testomatio_url')
        project = os.environ.get('TESTOMATIO')
        if project is None:
            pytest.exit('TESTOMATIO env variable is not set')
        ## TODO: move connector tin testomatio
        pytest.connector = Connector(url, project) # backward compatibility
        pytest.testomatio.connector = pytest.connector
        if config.getoption('testRunEnv'):
            pytest.testomatio.test_run.set_env(config.getoption('testRunEnv'))


def pytest_collection_modifyitems(session: Session, config: Config, items: list[Item]) -> None:
    if config.getoption(testomatio):
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
                pytest.exit(
                    f'{len(items)} found. {len(meta)} unique test functions data collected and updated.'
                    f'Exit without test execution')
            case 'remove':
                mapping = get_test_mapping(meta)
                for test_file in test_files:
                    update_tests(test_file, mapping, test_names, decorator_name, remove=True)
                pytest.exit(
                    f'{len(items)} found. tests ids removed. Exit without test execution')
            case 'report':
                if pytest.testomatio.test_run.id:
                    run_details = pytest.testomatio.connector.update_test_run(**pytest.testomatio.test_run.to_dict())
                else:
                    # TODO: don't create test run for shared execution
                    run_details = pytest.testomatio.connector.create_test_run(**pytest.testomatio.test_run.to_dict())
                    pytest.testomatio.test_run.set_run_id(run_details['uid'])
                
                if run_details is None:
                    log.error('Test run failed to create. Reporting skipped')
                    return

                if run_details.get('artifacts'):
                    s3_access_key = os.environ.get('ACCESS_KEY_ID') or run_details['artifacts'].get('ACCESS_KEY_ID')
                    s3_secret_key = os.environ.get('SECRET_ACCESS_KEY') or run_details['artifacts'].get('SECRET_ACCESS_KEY')
                    s3_endpoint = os.environ.get('ENDPOINT') or run_details['artifacts'].get('ENDPOINT')
                    s3_bucket = os.environ.get('BUCKET') or run_details['artifacts'].get('BUCKET')
                    if all((s3_access_key, s3_secret_key, s3_endpoint, s3_bucket)):
                        pytest.testomatio.set_s3_connector(S3Connector(s3_access_key, s3_secret_key, s3_endpoint, s3_bucket))
                        pytest.testomatio.s3_connector.login()
                        pytest.s3_connector = pytest.testomatio.s3_connector # backward compatibility
                    else:
                        pytest.testomatio.set_s3_connector(S3Connector('', '', '', ''))
                        pytest.s3_connector = pytest.testomatio.s3_connector # backward compatibility
            case 'debug':
                with open(metadata_file, 'w') as file:
                    data = json.dumps([i.to_dict() for i in meta], indent=4)
                    file.write(data)
                pytest.exit(
                    f'saved metadata to {metadata_file}. Exit without test execution')
            case _:
                pytest.exit('Unknown pytestomatio parameter. Use one of: add, remove, sync, debug')


def pytest_runtest_makereport(item: Item, call: CallInfo):
    pytest.testomatio_config_option = item.config.getoption(testomatio)
    if pytest.testomatio_config_option is None or pytest.testomatio_config_option != 'report':
        return
    elif not pytest.testomatio.test_run.test_run_id:
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

    if item.nodeid not in pytest.testomatio.test_run.status_request:
        pytest.testomatio.test_run.status_request[item.nodeid] = request
    else:
        for key, value in request.items():
            if key == 'title' and call.when == 'teardown':
                continue
            if value is not None:
                pytest.testomatio.test_run.status_request[item.nodeid][key] = value


def pytest_runtest_logfinish(nodeid, location):
    if pytest.testomatio_config_option is None or pytest.testomatio_config_option != 'report':
        return
    elif not pytest.testomatio.test_run.test_run_id:
        return

    for nodeid, request in pytest.testomatio.test_run.status_request.items():
        if request['status']:
            pytest.testomatio.connector.update_test_status(run_id=pytest.testomatio.test_run.test_run_id, **request)
    pytest.testomatio.test_run.status_request = {}


def pytest_sessionfinish(session: Session, exitstatus: int):
    if os.environ.get('TESTOMATIO_RUN'):
        return
    if pytest.testomatio.test_run.test_run_id:
        pytest.testomatio.connector.finish_test_run(pytest.testomatio.test_run.test_run_id)
