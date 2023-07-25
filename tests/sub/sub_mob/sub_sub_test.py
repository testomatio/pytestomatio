from pytest import mark


def test_pass_sub_sub():
    assert 2 + 2 == 4


def test_pass_fix_sub_sub(dummy_fixture):
    assert 3 + 3 == 6


def test_fail_sub_sub():
    assert 2 + 2 == 11


@mark.parametrize('data', [1, 2, 3, 4, 5, 'a'])
def test_ddt_parametrized_sub_sub(data):
    assert str(data).isnumeric()


@mark.skip
def test_skip_sub_sub():
    n = 3
    p = 7
    assert n * p == 21
