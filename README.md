[![Support Ukraine Badge](https://bit.ly/support-ukraine-now)](https://github.com/support-ukraine/support-ukraine)

# testomat.io plugin for pytest

## uses testomat.io API:

- https://testomatio.github.io/check-tests/
- https://testomatio.github.io/reporter/

## Installation

```bash
pip install pytestomatio
```

## Usage

Synchronize tests to testomat.io and get back test id.
Tests will not be executed

```bash
pytest --testomatio sync
```

Remove all test ids from source code. Tests will not be executed

```bash
pytest --testomatio remove
```

Run pytest and send test results into testomat.io.  
Test can be sent to testomat.io without ids in your test code. If testomat.io failed to match tests by title, it will create
new tests for the run

```bash
pytest --testomatio report
```

Run pytest with debug parameter to get test data collected in metadata.json file

```bash
pytest --testomatio debug
```

## configuration
Create environment variable `TESTOMATIO` and set your testomat.io API key.
```bash
TESTOMATIO=<key>
```
Select code style by set environment variable `TESTOMATIO_CODE_STYLE`. Available options are 'default' and 'pep8'  
If you are not sure, don't set this variable. Default value is 'default'
```bash
TESTOMATIO_CODE_STYLE=pep8
```
Set test run name in Testomat.io
```bash
TESTOMATIO_RUN=test_run_name
```
Set test run environment in Testomat.io
```bash
TESTOMATIO_ENV=linux,chrome,1920x1080
```
Set test run labels in Testomat.io
TESTOMATIO_LABELS=smoke,regression

```bash


### Run groups parameter
There is environment variable `TESTOMATIO_RUNGROUP_TITLE` that can be used to specify run tests with specific group title.

### pytest.ini
In case you are using private testomat.io service, create `pytest.ini` file in your project root directory. Specify
testomat.io url in it

```ini
[pytest]
testomatio_url = https://app.testomat.io

```

### Submitting Test Run Environment

to configure test environment, you can use additional option:

```bash
pytest --testomatio report --testRunEnv "windows11,chrome,1920x1080"
```

Environment values are comma separated, please use double quotation.


### Submitting Test Artifacts

testomat.io does not store any screenshots, logs or other artifacts.

In order to manage them it is advised to use S3 Buckets (GCP Storage).
https://docs.testomat.io/usage/test-artifacts/

Analyser needs to be aware of the cloud storage credentials.
There are two options:
1. Enable **Share credentials with testomat.io Reporter** option in testomat.io Settings -> Artifacts.
2. Use environment variables   `ACCESS_KEY_ID, SECRET_ACCESS_KEY, ENDPOINT, BUCKET`

You would need to decide when you want to upload your test artifacts to cloud storage

1) Upload page screenshot when test fails, using fixtures [reference](https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures)

```python
# content of conftest.py
import pytest
import random
import os
from typing import Dict
from pytest import StashKey, CollectReport
from playwright.sync_api import Page

phase_report_key = StashKey[Dict[str, CollectReport]]()

@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    rep = yield
    item.stash.setdefault(phase_report_key, {})[rep.when] = rep
    return rep


@pytest.fixture(scope="function")
def handle_artifacts(page: Page, request):
    yield
    report = request.node.stash[phase_report_key]
    if ("call" not in report) or report["setup"].failed or report["call"].failed:
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        filename = f"{random_string}.png"
        screenshot_path = os.path.join(artifacts_dir, filename)
        page.screenshot(path=screenshot_path)
        # file_path - required, path to file to be uploaded
        # file_bytes - required, bytes of the file to be uploaded
        # key - required, file name in the s3 bucket
        # bucket_name - optional,name of the bucket to upload file to. Default value is taken from testomat.io
        artifact_url = pytest.testomatio.upload_file(screenshot_path, filename)
        # or
        # artifact_url = pytest.testomatio.upload_file_object(file_bytes, key, bucket_name)
        pytest.testomatio.add_artifacts(request.node, [artifact_url])
    page.close()
```

⚠️ Please take into account s3_connector available only after **pytest_collection_modifyitems()** hook is executed.

2) If you prefer to use pytest hooks - add `pytest_runtest_makereport` hook in your `conftest.py` file.

```python
def pytest_runtest_makereport(item, call):
    artifact_url = pytest.testomatio.upload_file(screenshot_path, filename)
    pytest.testomatio.add_artifacts([artifact_url])
```

### Clarifications

- tests can be synced even without `@patest.mark.testomatio('@T96c700e6')` decorator.
- test title in testomat.io == test name in pytest
- test suit title in testomat.io == test file name in pytest

## Example of test

To make the experience more consistent, it uses standard pytest markers.  
testomat.io test id is a string value that starts with `@T` and has 8 symbols after.

```python
from pytest import mark


@mark.testomatio('@T96c700e6')
def test_example():
    assert 2 + 2 == 4
```

### Compatibility table with [Testomatio check-tests](https://github.com/testomatio/check-tests)

| Action |  Compatibility | Method |
|--------|--------|-------|
| Importing test into testomat.io | complete | `pytest --testomatio sync` |
| Exclude hook code of a test | N/A | N/A |
| Include line number code of a test | N/A | N/A |
| Import Parametrized Tests | complete | default behaviour |
| Disable Detached Tests | complete | `pytest --testomatio sync --no-detached` |
| Synchronous Import | complete | default behaviour |
| Auto-assign Test IDs in Source Code | complete | default behaviour |
| Keep Test IDs Between Projects | complete | `pytest --testomatio sync --create` |
| Clean Test IDs | complete | `pytest --testomatio remove` |
| Import Into a Branch | N/A | N/A |
| Keep Structure of Source Code | complete | `pytest --testomatio sync --keep-structure` |
| Delete Empty Suites | complete | `pytest --testomatio sync --no-empty` |
| Import Into a Specific Folder | complete | `pytest --testomatio --directory "Windows\smoke"` |
| Debugging | parity | `pytest --testomatio debug` |


## Test
- import into empty project
- updated test - (resync)
- test run
- test run into a folder
- test run labels, tags

## TODO
- Fix test duration
- Require more back references from testomatio
- pytest.skip should behave as @pytest.mark.skip
- Refactor test run and make run url available

## Contribution
1. `pip install -e .`
2. `cz commit`
3. `cz bump`
4. `git push remoteName branchName --tags`