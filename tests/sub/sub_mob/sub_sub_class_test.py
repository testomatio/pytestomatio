from pytest import mark
import pytest


class TestClassSubSub:

    @pytest.mark.testomatio("@T7e1cf6d3")
    def test_one_pass_sub(self):
        x = 'this'
        assert 'h' in x

    @pytest.mark.testomatio("@T64c0abec")
    def test_two_fail_sub(self):
        x = 'hello'
        assert hasattr(x, 'check')

    @pytest.mark.testomatio("@Ta488bdcb")
    @mark.skip
    def test_three_skip_sub(self, dummy_fixture):
        x = 'hello'
        assert hasattr(x, 'check')
