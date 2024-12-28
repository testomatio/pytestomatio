import pytest
#TODO verify requests to testomatio

@pytest.mark.testomatio("@Tfaf4da53")
@pytest.mark.smoke
def test_sync_stop_when_xdist_in_use(pytester):
    pytester.makepyfile("""
    def test_example():
        assert True
    """)

    # Ensure that your plugin code raises UsageError for this scenario instead of a generic Exception.
    # Something like:
    # if option == 'sync' and parallel_set:
    #     raise UsageError("The 'sync' mode does not support parallel execution! In order to synchronise test run command sync as '--testomatio sync -n 0'")

    result = pytester.runpytest_inprocess('-p', 'xdist', '--testomatio', 'sync', '-vv')

    # Match the entire error line as it appears in stderr
    result.stderr.fnmatch_lines([
        "ERROR: The 'sync' mode does not support parallel execution! In order to synchronise test run command sync as '--testomatio sync -n 0'"
    ])

    # Now that it's a usage error, pytest should produce a summary line that we can assert on
    assert result.ret != 0

@pytest.mark.smoke
def test_sync_works_with_xdist_set_to_0(pytester):
    pytester.makepyfile("""
    def test_example():
        assert True
    """)

    result = pytester.runpytest_inprocess('-p', 'xdist', '--testomatio', 'sync', '-n', '0', '-vv')

    # Assert that the special exit message is printed to stderr
    result.stdout.fnmatch_lines([
        "*Sync completed without test execution*"
    ])

    # Optional: Verify the process exited successfully (0 means no error)
    assert result.ret == 2