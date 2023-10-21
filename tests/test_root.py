from pytest import mark, fixture


@fixture
def some_fixture():
    yield


@mark.testomatio('@T67a02d9f')
def test_pass(some_fixture):
    import time
    assert 2 + 2 == 4


@mark.testomatio('@T4e2f8df1')
def test_pass_fix(dummy_fixture):
    assert 3 + 3 == 6


@mark.testomatio('@Tefe6c6a2')
def test_fail():
    assert 2 + 2 == 11


@mark.testomatio('@Tca8a4366')
@mark.parametrize('data', [8, 1, 2, 3, 4, 5, 'a', b'123', b'asdasd', {'hello': 'world'}, [1, 2, 3]])
def test_ddt_parametrized(data):
    assert str(data).isnumeric()


@mark.testomatio('@Tc5045fa6')
@mark.skip
def test_skip():
    n = 3
    p = 7
    assert n * p == 21


class TestClassCom:

    @mark.testomatio('@T7716c8f8')
    def test_cls_same_file(self):
        assert True
