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

    result = pytester.runpytest("--testomatio", "report", "-vv")
    result.assert_outcomes(passed=2, failed=0, skipped=0)
    assert "test_callable_in_params.py::test_operations[add-2-3-5] PASSED" in result.stdout.str()
    assert "test_callable_in_params.py::test_operations[multiply-2-3-6] PASSED" in result.stdout.str()

