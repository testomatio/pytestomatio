from os import getenv
from os.path import basename
from pytest import Item
from pytestomatio.testomatio.testomat_item import TestomatItem
from pytestomatio.testing.testItem import TestItem
from pytestomatio.decor.decorator_updater import update_tests
from pytestomatio.testing.code_collector import get_functions_source_by_name
from re import sub


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
            if not tcm_test.file_name:
                continue
            # Test that are synced into user specified folder - might end up with altered file path in testomatio
            # making file path not match between source code and testomatio
            # to mitigate this we compare only file names, skipping the path
            # while it works it might not be the most reliable approach
            # however, the underlying issue is the ability to alter the file path in testomatio
            # https://github.com/testomatio/check-tests?tab=readme-ov-file#import-into-a-specific-suite
            if test.resync_title == tcm_test.title and basename(test.file_name) == basename(tcm_test.file_name):
                test.id = tcm_test.id
                tcm_test_data.remove(tcm_test)
                break

    mapping = get_test_mapping(meta)
    for test_file in test_files:
        update_tests(test_file, mapping, test_names, decorator_name)


def read_env_s3_keys(testRunConfig: dict) -> tuple:
    artifacts = testRunConfig.get('artifacts', {})
    bucket_path = (getenv('BUCKET_PATH') or getenv('S3_BUCKET_PATH'))
    acl = 'private' if (getenv('TESTOMATIO_PRIVATE_ARTIFACTS') or artifacts.get('presign')) else "public-read"
    return (
        getenv('REGION') or getenv('S3_REGION') or artifacts.get('REGION'),
        getenv('ACCESS_KEY_ID') or getenv('S3_ACCESS_KEY_ID') or artifacts.get('ACCESS_KEY_ID'),
        getenv('SECRET_ACCESS_KEY') or getenv('S3_SECRET_ACCESS_KEY') or artifacts.get('SECRET_ACCESS_KEY'),
        getenv('ENDPOINT') or  getenv('S3_ENDPOINT') or artifacts.get('ENDPOINT'),
        getenv('BUCKET') or getenv('S3_BUCKET') or artifacts.get('BUCKET'),
        bucket_path + "/" + testRunConfig.get("uid") if bucket_path else testRunConfig.get("uid"),
        acl
    )

def safe_string_list(param: str):
    if not param:
        return None
    return ",".join([sub(r"\s", "", part) for part in param.split(',')])
