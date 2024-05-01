import os
from pytestomatio.decor.pep8 import update_tests as update_tests_pep8
from pytestomatio.decor.default import update_tests as update_tests_default


def update_tests(file: str,
                 mapped_tests: list[tuple[str, int]],
                 all_tests: list[str],
                 decorator_name: str,
                 remove=False):
    code_style = os.getenv('TESTOMATIO_CODE_STYLE', 'default')
    if code_style == 'pep8':
        update_tests_pep8(file, mapped_tests, all_tests, decorator_name, remove)
    else:
        update_tests_default(file, mapped_tests, all_tests, decorator_name, remove)
