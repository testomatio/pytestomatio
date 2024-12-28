import pytest
pytestmark = pytest.mark.smoke

test_file = """
        import pytest

        def test_smoke():
            pass

        @pytest.mark.testomatio("@T123")
        def test_testomatio_only():
            pass

        @pytest.mark.testomatio("@T456")
        def test_smoke_and_testomatio():
            pass

        def test_neither_marker():
            pass
"""

@pytest.mark.testomatio("@T7b058966")
def test_cli_param_test_id_without_filters(pytester):
    pytester.makepyfile(test_file)

    result = pytester.runpytest("--testomatio", "report", "-vv")
    result.assert_outcomes(passed=4, failed=0, skipped=0)
    result.stdout.fnmatch_lines([
        "*::test_smoke PASSED*",
        "*::test_testomatio_only PASSED*",
        "*::test_smoke_and_testomatio PASSED*",
        "*::test_neither_marker PASSED*",
    ])

@pytest.mark.testomatio("@T3cf626ca")
def test_cli_param_test_id_with_k_filter(pytester):
    pytester.makepyfile(test_file)

    result = pytester.runpytest("--testomatio" ,"report", "-vv", "-k", "test_neither_marker")
    result.assert_outcomes(passed=1, failed=0, skipped=0)
    result.stdout.fnmatch_lines([
        "*::test_neither_marker PASSED*",
    ])

@pytest.mark.testomatio("@T709adc8a")
def test_cli_param_test_id_without_k_filter_matching_2_tests(pytester):
    pytester.makepyfile(test_file)

    result = pytester.runpytest("--testomatio", "report", "-vv", "-k", "test_smoke")
    result.assert_outcomes(passed=2, failed=0, skipped=0)
    result.stdout.fnmatch_lines([
        "*::test_smoke PASSED*",
        "*::test_smoke_and_testomatio PASSED*",
    ])

# TODO: troubleshoot pytester env
# The testomatio and test-id parameters are lost in the pytester env.
# Please test it in a semiautomated way with "test_cli_params.py" test
@pytest.mark.testomatio("@T5a965adf")
def test_cli_param_test_id_with_test_id_filter(pytester):
    pytest.skip()
    pytester.makepyfile(test_file)

    result = pytester.runpytest_inprocess("--testomatio", "report", '--test-id="@T123"', "-vv")
    result.assert_outcomes(passed=1, failed=0, skipped=0)
    result.stdout.fnmatch_lines([
        "*::test_testomatio_only PASSED*",
    ])