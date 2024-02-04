from pytest import Item
from .testomat_item import TestomatItem
from .testItem import TestItem
from .decorator_updater import update_tests
from .code_collector import get_functions_source_by_name


def collect_tests(items: list[Item]):
    meta: list[TestItem] = list()
    test_files: set = set()
    test_names: list = list()
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
    return meta, test_files, test_names


def get_test_mapping(tests: list[TestItem]) -> list[tuple[str, int]]:
    return [(test.title, test.id) for test in tests]


def parse_test_list(raw_response: dict) -> list[TestomatItem]:
    suites = set([suite for suite in raw_response['suites'].keys() if '#' not in suite])
    result = dict()
    for key, value in raw_response['tests'].items():
        test = result.get(value)
        if test is None:
            test = {
                'name': None,
                'suite': None,
                'file': None
            }
        parts = [part for part in key.split('#') if part != '']
        if len(parts) == 1:
            test['name'] = parts[0]
        elif len(parts) == 2:
            if parts[0] in suites:
                test['suite'] = parts[0]
            test['name'] = parts[1]
        elif len(parts) == 3:
            test['file'] = parts[0]
            test['name'] = parts[-1]
        result[value] = test
    return [TestomatItem(id, test['name'], test['file']) for id, test in result.items()]


def add_and_enrich_tests(meta: list[TestItem], test_files: set,
                         test_names: list, testomatio_tests: dict, decorator_name: str):
    # set test ids from testomatio to test metadata
    tcm_test_data = parse_test_list(testomatio_tests)
    for test in meta:
        for tcm_test in tcm_test_data:
            if test.title == tcm_test.title and test.file_name == tcm_test.file_name:
                test.id = tcm_test.id
                tcm_test_data.remove(tcm_test)
                break

    mapping = get_test_mapping(meta)
    for test_file in test_files:
        update_tests(test_file, mapping, test_names, decorator_name)
