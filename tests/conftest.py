from pytest import mark
from pytest import fixture


@fixture
def dummy_fixture():
    print('before')
    yield
    print('after')


@mark.testomatio('@T6a2dfc31')
def test_one_pass_new():
    x = 'this'
    assert 'h' in x
