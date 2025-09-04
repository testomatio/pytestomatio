from pytest import mark


class TestClass:

    @mark.testomatio('@T4a0527af')
    def test_one_pass(self):
        x = 'this'
        assert 'h' in x

    @mark.testomatio('@T4bc8a939')
    def test_two_fail(self):
        x = 'hello'
        assert hasattr(x, 'check')

    @mark.testomatio('@T3dd32910')
    @mark.skip
    def test_three_skip(self):
        x = 'hello'
        assert hasattr(x, 'check')
