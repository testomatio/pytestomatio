# pytest --testomatio report tests  --test-id="@T123" -k test_smoke
# verify 3 test passes
# tests/test_cli_params.py::test_smoke PASSED                                                              [ 33%]
# tests/test_cli_params.py::test_smoke_and_testomatio PASSED                                               [ 66%]
# tests/test_cli_params.py::test_testomatio_only PASSED                                                    [100%]
#
# ======================================= 3 passed, 50 deselected in 0.89s =======================================

import pytest

@pytest.mark.testomatio("@T55ecbca9")
def test_smoke():
    pass

@pytest.mark.testomatio("@T123")
def test_testomatio_only():
    pass

@pytest.mark.testomatio("@T456")
def test_smoke_and_testomatio():
    pass

@pytest.mark.testomatio("@T06f3da52")
def test_neither_marker():
    pass