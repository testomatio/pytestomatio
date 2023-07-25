from pytest import fixture


@fixture
def dummy_fixture():
    print('before')
    yield
    print('after')
