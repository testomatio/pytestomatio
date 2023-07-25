import sys

import pytest
import json
from pytest import Parser, Session, Config, Item
from analyzer.testomatio import Connector, update_tests
from analyzer.testItem import TestItem
from analyzer.testomatio.code_collector import get_functions_source_by_name

metadata_file = 'metadata.json'
decorator_name = 'testomatio'


def pytest_addoption(parser: Parser) -> None:
    parser.addoption('--analyzer',
                     action='store_true',
                     help='saves json with tests metadata to the root folder')
    parser.addoption('--testomatio',
                     action='store',
                     default=None,
                     help='align tests with testomat.io. Use parameters: add - to create or update, clear - to remove')
    parser.addini('testomatio_url', 'testomat.io base url', default='https://app.testomat.io')
    parser.addini('testomatio_project', 'testomat.io project api key')
    parser.addini('testomatio_email', 'testomat.io user email')
    parser.addini('testomatio_password', 'testomat.io user password')



def pytest_configure(config: Config):
    config.addinivalue_line(
        "markers", "testomatio(arg): built in marker to connect test case with testomat.io by unique id"
    )


def pytest_collection_modifyitems(session: Session, config: Config, items: list[Item]) -> None:
    meta: list[TestItem] = list()
    test_files: set = set()
    test_names: list = list()
    if config.getoption('analyzer'):
        parameter_filter: set[Item] = set()
        for item in items:
            if item.function not in parameter_filter:
                parameter_filter.add(item.function)
                ti = TestItem(item)
                test_files.add(ti.abs_path)
                test_names.append(ti.title)
                meta.append(ti)

        for test_file in test_files:
            pairs = [p for p in get_functions_source_by_name(test_file, test_names)]
            for ti in meta:
                for name, source_code in pairs:
                    if ti.title == name and ti.abs_path == test_file:
                        ti.source_code = source_code
                        break

        with open(metadata_file, 'w') as file:
            data = json.dumps([i.to_dict() for i in meta], indent=4)
            file.write(data)

    if config.getoption('testomatio') and config.getoption('analyzer'):
        match config.getoption('testomatio'):
            case 'add':
                connector = Connector()
                connector.connect('oleksii.ostapov@gmail.com', 'bv!23L8Wgd9Vwb!')
                connector.enrich_test_with_ids(api_key='70t3da349fte', test_metadata=meta)
                connector.disconnect()
                mapping = get_test_mapping(meta)
                for test_file in test_files:
                    update_tests(test_file, mapping, test_names, decorator_name)
            case 'clear':
                mapping = get_test_mapping(meta)
                for test_file in test_files:
                    update_tests(test_file, mapping, test_names, decorator_name, remove=True)
            case 'default':
                # todo any options?
                pass

    pytest.exit(f'{len(items)} found. {len(meta)} unique test functions data collected. Exit without test execution')


def add_decorators(files, mapping, tests):
    for test_file in files:
        update_tests(test_file, mapping, tests, decorator_name)


def get_test_mapping(tests: list[TestItem]) -> list[tuple[str, int]]:
    return [(test.title, test.id) for test in tests]
