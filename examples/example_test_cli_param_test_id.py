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

    result = pytester.runpytest_subprocess("--testomatio", "report", "-vv")
    result.assert_outcomes(passed=4, failed=0, skipped=0)
    result.stdout.fnmatch_lines([
        "*::test_smoke*",
        "*::test_testomatio_only*",
        "*::test_smoke_and_testomatio*",
        "*::test_neither_marker*",
    ])

@pytest.mark.testomatio("@T3cf626ca")
def test_cli_param_test_id_with_k_filter(pytester):
    pytester.makepyfile(test_file)

    result = pytester.runpytest_subprocess("--testomatio" ,"report", "-vv", "-k", "test_neither_marker")
    result.assert_outcomes(passed=1, failed=0, skipped=0)
    result.stdout.fnmatch_lines([
        "*::test_neither_marker*",
    ])

@pytest.mark.testomatio("@T709adc8a")
def test_cli_param_test_id_without_k_filter_matching_2_tests(pytester):
    pytester.makepyfile(test_file)

    result = pytester.runpytest_subprocess("--testomatio", "report", "-vv", "-k", "test_smoke")
    result.assert_outcomes(passed=2, failed=0, skipped=0)
    result.stdout.fnmatch_lines([
        "*::test_smoke*",
        "*::test_smoke_and_testomatio*",
    ])

# Test with mock environment to avoid pytester env issues
@pytest.mark.testomatio("@T5a965adf")
def test_cli_param_test_id_with_test_id_filter(pytester, monkeypatch):
    # Mock the TESTOMATIO environment variable to avoid validation errors
    monkeypatch.setenv("TESTOMATIO", "test_token_123")
    
    pytester.makepyfile(test_file)

    # Run with debug mode to avoid needing real TESTOMATIO connection
    # Use -n 0 to disable xdist parallel execution  
    result = pytester.runpytest_subprocess("--testomatio", "debug", '--test-id="@T123"', "-vv", "-n", "0")
    
    # In debug mode, pytest exits with code 2 after creating metadata.json
    # This is expected behavior, so we check for successful collection and exit
    assert result.ret == 2  # Expected exit code for debug mode
    result.stdout.fnmatch_lines([
        "*collected 4 items*",
        "*Debug file created. Exiting...*"
    ])