from pytest import mark


class TestClass:

    def test_one_pass(self):
        x = 'this'
        assert 'h' in x

    def test_two_fail(self):
        x = 'hello'
        assert hasattr(x, 'check')

    @mark.skip
    def test_three_skip(self):
        x = 'hello'
        assert hasattr(x, 'check')
