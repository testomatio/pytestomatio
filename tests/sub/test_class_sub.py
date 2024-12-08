from pytest import mark


class TestClassSub:

    @mark.testomatio("@T7e1cf6d3")
    def test_one_pass_sub(self):
        x = 'this'
        assert 'h' in x

    @mark.testomatio("@T64c0abec")
    def test_two_fail_sub(self):
        x = 'hello'
        assert hasattr(x, 'check')

    @mark.testomatio("@Ta488bdcb")
    @mark.skip
    def test_three_skip_sub(self):
        x = 'hello'
        assert hasattr(x, 'check')
