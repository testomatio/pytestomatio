[![Support Ukraine Badge](https://bit.ly/support-ukraine-now)](https://github.com/support-ukraine/support-ukraine)

# Testomat.io plugin for pytest

## uses Testomat.io API:

- https://testomatio.github.io/check-tests/
- https://testomatio.github.io/reporter/

## Installation

```bash
pip install pytest-analyzer
```

## configuration

Create environment variable `TESTOMATIO` and set your testomat.io API key.
Linux:

```bash
export TESTOMATIO=<key>
```

Windows (cmd):

```bash
set TESTOMATIO=<key>
```

### Run groups parameter
There is environment variable `TESTOMATIO_RUNGROUP_TITLE` that can be used to specify run tests with specific group title.

### pytest.ini
In case you are using private testomat.io service, create `pytest.ini` file in your project root directory. Specify
testomat.io url in it

```ini
[pytest]
testomatio_url = https://app.testomat.io

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
Sync can be executed even without marking tests with ids. If testomat.io failed to match tests by title, it will create
new tests for the run

```bash
pytest --analyzer sync
```

Run pytest with analyzer debug parameter to get test data collected in metadata.json file

```bash
pytest --analyzer debug
```

### Submitting Test Run Environment

to configure test environment, you can use additional option:

```bash
pytest --analyzer sync --testRunEnv windows11,chrome,1920x1080
```

### Submitting Test Artifacts (NEW)

According documentation, Testomat.io does not store any screenshots,
logs or other artifacts. In order to manage them it is advised to use S3 Buckets.
https://docs.testomat.io/usage/test-artifacts/

In order to save artifacts, enable **Share credentials with Testomat.io Reporter** option in testomat.io Settings ->
Artifacts.

To send artifact to s3 bucket, next code should be added to test:

```python
# file_path - path to file to be uploaded
# file_bytes - bytes of the file to be uploaded
# key - file name in the s3 bucket
# bucket_name - name of the bucket to upload file to. If not set, bucket name from pytest.ini will be used, if set, overrides bucket name from pytest.ini
artifact_url = pytest.s3_connector.upload_file(file_path, key, bucket_name)
# or
artifact_url = pytest.s3_connector.upload_file_object(file_bytes, key, bucket_name)
```

⚠️ Please take into account s3_connector available only after **pytest_collection_modifyitems()** hook is executed.

In conftest.py file next hook can be added. set attribute testomatio_artifacts. This list will be sent to testomat.io

```python
def pytest_runtest_makereport(item, call):
    artifact_urls = ['url1', 'url2']
    setattr(item, 'testomatio_artifacts', artifact_urls)
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

## Change log

### 1.3.0 - added artifacts support connector
- [issue 5](https://github.com/Ypurek/pytest-analyzer/issues/5) - connection issues not blocking test execution anymore

### 1.2.8 - fixed issues
- [issue 4](https://github.com/Ypurek/pytest-analyzer/issues/4) - Analyzer's execution order

### 1.2.5 - fixed issues

- added env variable `TESTOMATIO_RUNGROUP_TITLE` to group test runs
- fixed serialization issue for update test status example

### 1.2.4 - improved parametrized tests reporting

- now parameters are passed to example attribute in the report

### 1.2.3 - fixed issue with test artifacts

- if no credentials provided, test artifacts will not be uploaded and no issue raised

### 1.2.0 - major update after testomat.io review

- code refactored
- simplified authentication. Only API key needed
- moved API key from pytest.ini to environment variable
- S3 credentials now read from testomat.io API, no local configuration needed
- Prettified test names in testomat.io

### 1.1.0 - added artifacts support connector

- there is possibility to add artifacts (screenshots, logs) to test report

### 1.0.9 - first public release
 
- test analyzer able to sync tests with testomat.io
- test analyzer able to add test ids to tests
- test analyzer able to submit test results to testomat.io

## Roadmap
- improve logging
