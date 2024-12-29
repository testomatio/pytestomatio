import pytest
pytestmark = pytest.mark.smoke

test_file = """
    import pytest

    # Define some dummy callables
    def add(a, b):
        return a + b

    def multiply(a, b):
        return a * b

    @pytest.mark.testomatio("@Tbca18714")
    @pytest.mark.parametrize(
        "operation, a, b, expected",
        [
            (add, 2, 3, 5),  # Test add function
            (multiply, 2, 3, 6),  # Test multiply function
        ],
    )
    def test_operations(operation, a, b, expected):
        # Call the provided operation
        result = operation(a, b)
        assert result == expected, f"Expected {expected}, got {result}"
"""

@pytest.mark.testomatio("@Tb8930394")
def test_callable_in_params(pytester):
    pytester.makepyfile(test_file)

    pytester.runpytest("--testomatio", "sync", "-n", "0", "--no-detach")
    result = pytester.runpytest("--testomatio", "report", "-vv")
    result.assert_outcomes(passed=2, failed=0, skipped=0)
    cleaned_lines = [line.strip() for line in result.stdout.lines if line.strip()]

    assert any("test_callable_in_params.py::test_operations[add-2-3-5]" in line for line in cleaned_lines)
    assert any("test_callable_in_params.py::test_operations[multiply-2-3-6]" in line for line in cleaned_lines)

session_fixture_file = """
    import pytest

    @pytest.fixture(scope="session", params=["db_connection_1", "db_connection_2"])
    def session_fixture(request):
        # Simulate setting up a database connection
        db_connection = request.param
        yield db_connection
        # Simulate tearing down the database connection

    def test_session_fixture_usage(session_fixture):
        assert session_fixture in ["db_connection_1", "db_connection_2"], (
            f"Unexpected session fixture value: {session_fixture}"
        )
"""

def test_session_fixture_with_param(pytester):
    pytester.makepyfile(session_fixture_file)

    pytester.runpytest("--testomatio", "sync", "-n", "0", "--no-detach")
    result = pytester.runpytest("--testomatio", "report", "-vv", "--full-trace")
    result.assert_outcomes(passed=2, failed=0, skipped=0)

    cleaned_lines = [line.strip() for line in result.stdout.lines if line.strip()]

    assert any("test_session_fixture_usage[db_connection_1]" in line for line in cleaned_lines)
    assert any("test_session_fixture_usage[db_connection_2]" in line for line in cleaned_lines)

