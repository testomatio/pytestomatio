from pytest import mark


@mark.testomatio('@T741f0586')
def test_something():
    assert 1 == 1


def test_no_decorator():
    assert 1 == 1