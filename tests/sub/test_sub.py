from pytest import mark


def test_pass_sub():
    assert 2 + 2 == 4


def test_pass_fix_sub(dummy_fixture):
    assert 3 + 3 == 6


def test_fail_sub():
    assert 2 + 2 == 11


@mark.parametrize('data', [1, 2, 3, 4, 5])
def test_ddt_parametrized_sub(data):
    assert str(data).isnumeric()


@mark.skip
def test_skip_sub():
    n = 3
    p = 7
    assert n * p == 21
