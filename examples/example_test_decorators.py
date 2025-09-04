from pytest import mark
import os


@mark.testomatio('@Ta44e5a34')
def test_something():
    assert 1 == 1


@mark.testomatio("@T81850b4b")
def test_no_decorator():
    assert 1 == 1


@mark.testomatio("@T9c91e8e7")
def test_some_test():
    x = os.getenv('TESTOMATIO_CODE_STYLE')
    assert x == 'pep8'
