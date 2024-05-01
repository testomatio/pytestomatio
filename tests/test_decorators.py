from pytest import mark
import os


@mark.testomatio('@T741f0586')
def test_something():
    assert 1 == 1


@mark.testomatio('@T8157d47d')
def test_no_decorator():
    assert 1 == 1


def test_some_test():
    x = os.getenv('TESTOMATIO_CODE_STYLE')
    assert x == 'pep8'
