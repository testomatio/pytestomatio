from pytest import mark, fixture


@fixture
def some_fixture():
    yield


@mark.testomatio('@T96c700e6')
def test_pass(some_fixture):
    import time
    assert 2 + 2 == 4


def test_pass_fix(dummy_fixture):
    assert 3 + 3 == 6


def test_fail():
    assert 2 + 2 == 11


@mark.parametrize('data', [1, 2, 3, 4, 5])
def test_ddt_parametrized(data):
    assert str(data).isnumeric()


@mark.skip
def test_skip():
    n = 3
    p = 7
    assert n * p == 21


class TestClassCom:

    def test_cls_same_file(self):
        assert True
