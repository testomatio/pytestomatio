from pytest import mark


@mark.testomatio("@T9c322c95")
def test_pass_sub():
    assert 2 + 2 == 4


@mark.testomatio("@T4e6f250b")
def test_pass_fix_sub(dummy_fixture):
    assert 3 + 3 == 6


@mark.testomatio("@T0bf7108d")
def test_fail_sub():
    assert 2 + 2 == 11


@mark.testomatio("@T7e069711")
@mark.parametrize('data', [1, 2, 3, 4, 5])
def test_ddt_parametrized_sub(data):
    assert str(data).isnumeric()


@mark.testomatio("@Tad0d98ed")
@mark.skip
def test_skip_sub():
    n = 3
    p = 7
    assert n * p == 21
