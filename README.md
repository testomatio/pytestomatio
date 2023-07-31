# Testomat.io plugin for pytest

## uses Testomat.io API:

- https://testomatio.github.io/check-tests/
- https://testomatio.github.io/reporter/

## Installation

```bash
pip install pytest-analyzer
```

## configuration

create `pytest.ini` file in your project root directory. Set next parameters:

```ini
[pytest]
testomatio_url = https://app.testomat.io ; this one is OPTIONAL
testomatio_project = 70t3da349fte ; project key is mandatory to assing tests to particular project
testomatio_email = example@test.com ; your login in testomat.io
testomatio_password = secure_password ; your password in testimat.io
```

## Usage

Run pytest with analyzer add parameter to analyze your tests, send them to testomat.io and get back test id. Tests will
not be executed

```bash
pytest --analyzer add
```

Run pytest with analyzer remove parameter to remove all test ids from your tests. Tests will not be executed

```bash
pytest --analyzer remove
```

Run pytest with analyzer sync parameter to execute tests and send the execution status to testomat.io.  
Sync can be executed even without marking tests with ids. If testomat.io failed to match tests by title, it will create new tests for the run

```bash
pytest --analyzer sync
```

Run pytest with analyzer debug parameter to get test data collected in metadata.json file

```bash
pytest --analyzer debug
```

### Advanced usage

to configure test environment, you can use additional option:

```bash
pytest --analyzer sync --testRunEnv windows11,chrome,1920x1080
```

Eny environments used in test run. Should be placed in comma separated list, NO SPACES ALLOWED.

### Clarifications

- tests can be synced even without `@mark.testomatio('@T96c700e6')` decorator.
- test title in testomat.io == test name in pytest
- test suit title in testomat.io == test file name in pytest

## Example of test

To make analyzer experience more consistent, it uses standard pytest markers.  
Testomat.io test id is a string value that starts with `@T` and has 8 symbols after.

```python
from pytest import mark


@mark.testomatio('@T96c700e6')
def test_example():
    assert 2 + 2 == 4
```

## Roadmap

- handle REST API exceptions
- support screenshot attachments
- improve logging